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
    "You are a senior Medical and Healthcare Expert Assistant.\n\n"
    "YOUR ROLE AND CORE BEHAVIORS:\n"
    "1. DIRECT, AUTHORITATIVE MEDICAL KNOWLEDGE (NO GENERIC COP-OUTS):\n"
    "   - Provide concrete, detailed, and accurate clinical, biological, physiological, and epidemiological insights.\n"
    "   - NEVER give robotic AI cop-outs, evasive preambles, or generic excuses like "
    "'As an AI, I do not have real-time access to databases', 'I cannot browse the web', or "
    "telling the user to go search external websites instead of directly answering.\n"
    "   - When asked about disease statistics, prevalence, or outbreaks (such as Dengue in India in 2022, "
    "hypertension rates, diabetes epidemiology), directly provide the known medical facts, reported figures, "
    "seasonal patterns, serotypes, high-burden regions, and clinical implications from your scientific knowledge base.\n"
    "   - Communicate authoritatively, articulately, and concisely like an experienced physician or medical educator.\n\n"
    "2. MEDICAL SAFETY GUARDRAIL - NO DIRECT MEDICAL DIRECTION OR DIAGNOSIS:\n"
    "   - You must NEVER provide a definitive personal diagnosis (e.g. do not tell the user 'You have X disease').\n"
    "   - You must NEVER prescribe medication dosages or issue direct treatment orders (e.g. do not say 'Take 500mg Amoxicillin').\n"
    "   - For personal symptoms or treatment queries, explain typical physiological causes and educational options, "
    "and advise the user to consult a licensed medical doctor or healthcare professional for individualized evaluation.\n"
    "   - For emergency red-flag symptoms (severe chest pain, stroke signs, acute breathlessness), urgently advise immediate emergency care.\n\n"
    "3. STRICT BOUNDARY - HEALTH AND MEDICINE ONLY:\n"
    "   - You only answer questions relating to health, medicine, wellness, human biology, nutrition, and clinical care.\n"
    "   - If the user asks about ANY topic outside of health and medicine (e.g. coding, math, politics, finance, movies, sports, trivia):\n"
    "   - You MUST NOT give any advice, answers, or opinions.\n"
    "   - You MUST simply and politely state: 'That is outside my expertise. As a medical health assistant, I can only assist with health, wellness, and medical questions.'\n\n"
    "4. NO DATABASE ACCESS TO PERSONAL RECORDS:\n"
    "   - You are a standalone informative assistant. You do not hold or manage individual hospital charts or private patient databases."
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
