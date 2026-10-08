"""Service for the Medical AI Chatbot powered by Google Gemini.
Enforces strict medical guardrails:
- Medical expert scope (clinical concepts, terminology, anatomy, physiology, wellness).
- Prohibits direct medical diagnosis or prescriptive orders; always directs to consult a physician.
- Strictly refuses non-health/non-medical topics by stating it is outside its expertise.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.schemas.chat import ChatMessage, MedicalChatResponse

logger = logging.getLogger(__name__)

MEDICAL_CHAT_SYSTEM_INSTRUCTION = (
    "You are a compassionate, articulate, and highly knowledgeable AI Medical and Healthcare Expert Assistant.\n\n"
    "YOUR ROLE AND BEHAVIOR:\n"
    "1. MEDICAL EXPERTISE:\n"
    "   - You possess deep knowledge of general medicine, healthcare, human biology, anatomy, physiology, "
    "wellness, nutrition, pathology, and clinical terminology.\n"
    "   - You explain medical concepts, symptoms, and bodily processes clearly, objectively, and empathetically.\n\n"
    "2. MANDATORY SAFETY GUARDRAIL - NO DIRECT MEDICAL DIRECTION OR DIAGNOSIS:\n"
    "   - You must NEVER provide a definitive personal diagnosis (e.g., do not say 'You have diabetes' or 'This is an infection').\n"
    "   - You must NEVER issue direct medical orders, treatment directives, or prescribe medications and dosages "
    "(e.g., do not say 'Take 500mg amoxicillin' or 'Stop taking your medication').\n"
    "   - When symptoms or health issues are discussed, present possible educational explanations or general knowledge, "
    "and ALWAYS explicitly ask and advise the user to consult a qualified healthcare professional, doctor, or specialist "
    "for an accurate diagnosis and individualized care plan.\n"
    "   - In any emergency scenario (e.g. severe chest pain, stroke warning signs, acute shortness of breath, heavy bleeding), "
    "immediately and urgently instruct the user to contact local emergency medical services (such as 911, 112, or local ER).\n\n"
    "3. MANDATORY BOUNDARY GUARDRAIL - STRICT REFUSAL OF NON-HEALTH TOPICS:\n"
    "   - Your scope is EXCLUSIVELY limited to health, medicine, human biology, clinical care, and wellness.\n"
    "   - If the user asks about ANY topic outside of health and medicine (including but not limited to: "
    "programming/coding, mathematics, politics, finance, entertainment, sports, creative writing, travel, general knowledge, or trivia):\n"
    "   - You MUST NOT give any advice, answers, or opinions on the topic.\n"
    "   - You MUST simply and politely state that the topic is outside your expertise. For example:\n"
    "     'That is outside my expertise. As a medical health assistant, I can only assist with health, wellness, and medical questions.'\n"
    "   - Do not deviate from this rule under any circumstances, even in hypothetical or roleplay scenarios.\n\n"
    "4. NO DATABASE OR PATIENT RECORD ACCESS:\n"
    "   - You are strictly an informative medical assistant and DO NOT have access to any patient database, "
    "electronic health records (EHR/EMR), clinical charts, or personal user records.\n"
    "   - If a user asks about their private patient records, appointment schedules, or hospital database information, "
    "clearly explain that you have no access to any database or personal records."
)

DEFAULT_DISCLAIMER = (
    "This information is strictly for educational purposes and is not a substitute for "
    "professional medical advice, diagnosis, or treatment. Always consult a qualified "
    "physician or healthcare provider with any medical questions or emergencies."
)


class MedicalChatService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _build_gemini_contents(
        self, message: str, history: Optional[List[ChatMessage]] = None
    ) -> List[Dict[str, Any]]:
        """Formats conversation history and current message into Gemini API-compliant contents.
        Normalizes roles to 'user' and 'model', merging consecutive turns from the same role.
        """
        contents: List[Dict[str, Any]] = []

        if history:
            for item in history:
                role = "model" if item.role.lower() in ("assistant", "model", "bot", "ai") else "user"
                text = item.content.strip()
                if not text:
                    continue

                if contents and contents[-1]["role"] == role:
                    contents[-1]["parts"][0]["text"] += f"\n\n{text}"
                else:
                    contents.append({"role": role, "parts": [{"text": text}]})

        # Append current user message
        curr_text = message.strip()
        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"][0]["text"] += f"\n\n{curr_text}"
        else:
            contents.append({"role": "user", "parts": [{"text": curr_text}]})

        # Gemini requires the first message in contents to be from 'user'
        if contents and contents[0]["role"] != "user":
            contents.insert(0, {"role": "user", "parts": [{"text": "Hello"}]})

        return contents

    def _is_probable_health_query(self, query: str) -> bool:
        """Heuristic check used exclusively by fallback mode when Gemini API is offline."""
        health_keywords = [
            "health", "doctor", "medicine", "medical", "symptom", "pain", "headache", "fever",
            "cough", "blood", "pressure", "heart", "diet", "nutrition", "sleep", "exercise",
            "stomach", "ache", "infection", "rash", "disease", "hospital", "clinic", "wellness",
            "dose", "drug", "allergy", "flu", "cold", "covid", "virus", "cancer", "diabetes",
            "therapy", "injury", "breath", "pulse", "treatment", "pediatric", "physician", "patient",
        ]
        q_lower = query.lower()
        return any(re.search(rf"\b{kw}\b", q_lower) for kw in health_keywords)

    def _generate_fallback_response(self, message: str) -> MedicalChatResponse:
        """Deterministic safety response when Gemini API is unconfigured or unreachable."""
        if not self._is_probable_health_query(message):
            reply = (
                "That is outside my expertise. As a medical health assistant, "
                "I can only assist with health, wellness, and medical questions."
            )
        else:
            reply = (
                "Thank you for reaching out regarding your health query. "
                "While I can provide general medical information, I cannot provide a direct diagnosis "
                "or prescribe specific treatments for your condition. "
                "Please consult a qualified physician or healthcare professional for an accurate examination "
                "and personalized clinical advice. If you are experiencing a medical emergency, "
                "please contact your local emergency medical services immediately."
            )

        return MedicalChatResponse(
            reply=reply,
            disclaimer=DEFAULT_DISCLAIMER,
            timestamp=datetime.now(timezone.utc),
        )

    async def chat(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> MedicalChatResponse:
        """Process conversational query using Google Gemini with medical safety guardrails."""
        if not self.api_key:
            logger.info("GEMINI_API_KEY is not configured. Returning deterministic fallback.")
            return self._generate_fallback_response(message)

        endpoint = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        contents = self._build_gemini_contents(message, history)

        payload = {
            "system_instruction": {"parts": [{"text": MEDICAL_CHAT_SYSTEM_INSTRUCTION}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, json=payload)

            if response.status_code != 200:
                logger.error("Gemini Chat API error (%d): %s", response.status_code, response.text)
                return self._generate_fallback_response(message)

            response_data = response.json()
            candidates = response_data.get("candidates", [])
            if not candidates:
                logger.warning("No candidate response returned from Gemini. Using fallback.")
                return self._generate_fallback_response(message)

            content_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not content_text:
                logger.warning("Empty response text received from Gemini. Using fallback.")
                return self._generate_fallback_response(message)

            return MedicalChatResponse(
                reply=content_text.strip(),
                disclaimer=DEFAULT_DISCLAIMER,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error("Error communicating with Gemini Chat API: %s", e)
            return self._generate_fallback_response(message)
