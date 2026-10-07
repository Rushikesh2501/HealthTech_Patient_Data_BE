"""Database seeding script for local development and testing.
Seeds initial accounts (Admin, Clinician, Nurse), anonymized patients, and realistic clinical encounters.
"""

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.constants import (
    AuditAction,
    AuditStatus,
    EncounterStatus,
    Gender,
    PatientStatus,
    UserRole,
)
from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.encounter import Encounter
from app.models.patient import Patient
from app.models.user import User


def seed_database():
    db = SessionLocal()
    try:
        print("--- Seeding HealthTech Database ---")

        # 1. Users
        default_password_hash = hash_password("HealthTech123!")

        users_to_seed = [
            {
                "email": "admin@healthtech.local",
                "name": "Dr. Sarah Jenkins (Admin)",
                "role": UserRole.ADMIN,
            },
            {
                "email": "doctor@healthtech.local",
                "name": "Dr. Rajesh Sharma",
                "role": UserRole.CLINICIAN,
            },
            {
                "email": "nurse@healthtech.local",
                "name": "Nurse Priya Nair",
                "role": UserRole.NURSE,
            },
        ]

        user_objects = []
        for u in users_to_seed:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    name=u["name"],
                    password_hash=default_password_hash,
                    role=u["role"],
                    is_active=True,
                )
                db.add(user)
                db.flush()
                user_objects.append(user)
                print(f"Created user: {u['email']} [{u['role'].value}]")
            else:
                user_objects.append(existing)
                print(f"User exists: {u['email']}")

        clinician_user = user_objects[1]
        admin_user = user_objects[0]

        # 2. Anonymized Patients (PT-0001 to PT-0025)
        existing_patient_count = db.query(Patient).count()
        patient_objects = []

        if existing_patient_count == 0:
            print("Creating 25 anonymized patient profiles...")
            base_date = datetime.now(timezone.utc).date() - timedelta(days=90)
            genders = [Gender.MALE, Gender.FEMALE, Gender.OTHER]
            sample_names = [
                "Aarav Sharma", "Pooja Patel", "Ramesh Kumar", "Sunita Devi", "Vikram Singh",
                "Ananya Iyer", "Rajesh Verma", "Meera Joshi", "Amitabh Das", "Deepika Reddy",
                "Suresh Nair", "Kavita Rao", "Manoj Gupta", "Rekha Menon", "Sanjay Choudhury",
                "Priya Kulkarni", "Arjun Bhat", "Geeta Pillai", "Naveen Chawla", "Shobha Roy",
                "Alok Mishra", "Divya Sen", "Kishore Pandey", "Preeti Saxena", "Harish Sethi"
            ]

            for i in range(1, 26):
                pt_code = f"PT-{i:04d}"
                age = random.choice([7, 12, 19, 24, 32, 45, 52, 61, 74])
                gender = random.choice(genders)
                reg_date = base_date + timedelta(days=random.randint(0, 85))
                name = sample_names[i - 1]

                p = Patient(
                    patient_code=pt_code,
                    name=name,
                    age=age,
                    gender=gender.value,
                    registration_date=reg_date,
                    status=PatientStatus.ACTIVE.value,
                )
                db.add(p)
                db.flush()
                patient_objects.append(p)
            print("25 patient profiles created.")
        else:
            patient_objects = db.query(Patient).order_by(Patient.id).all()
            print(f"Existing {len(patient_objects)} patients found.")
            sample_names = [
                "Aarav Sharma", "Pooja Patel", "Ramesh Kumar", "Sunita Devi", "Vikram Singh",
                "Ananya Iyer", "Rajesh Verma", "Meera Joshi", "Amitabh Das", "Deepika Reddy",
                "Suresh Nair", "Kavita Rao", "Manoj Gupta", "Rekha Menon", "Sanjay Choudhury",
                "Priya Kulkarni", "Arjun Bhat", "Geeta Pillai", "Naveen Chawla", "Shobha Roy",
                "Alok Mishra", "Divya Sen", "Kishore Pandey", "Preeti Saxena", "Harish Sethi"
            ]
            updated_count = 0
            for idx, p in enumerate(patient_objects):
                if not p.name:
                    p.name = sample_names[idx % len(sample_names)]
                    updated_count += 1
            if updated_count > 0:
                db.flush()
                print(f"Assigned names to {updated_count} existing patients.")

        # 3. Clinical Encounters
        existing_encounter_count = db.query(Encounter).count()
        if existing_encounter_count == 0 and patient_objects:
            print("Creating realistic clinical encounters...")

            clinical_cases = [
                {
                    "diagnosis": "Upper Respiratory Tract Infection",
                    "symptoms": "Cough, sore throat, low-grade fever for 3 days",
                    "treatment": "Amoxicillin 500mg TDS, Paracetamol 650mg, warm saline gargles",
                    "temperature": "100.2 °F",
                    "blood_pressure": "120/80 mmHg",
                },
                {
                    "diagnosis": "Type 2 Diabetes Mellitus",
                    "symptoms": "Polydipsia, increased fatigue, polyuria",
                    "treatment": "Metformin 500mg BD after food, dietary glycemic counseling",
                    "temperature": "98.4 °F",
                    "blood_pressure": "134/86 mmHg",
                },
                {
                    "diagnosis": "Essential Hypertension",
                    "symptoms": "Mild occipital headache, dizziness",
                    "treatment": "Amlodipine 5mg OD morning, low sodium diet recommended",
                    "temperature": "98.6 °F",
                    "blood_pressure": "152/94 mmHg",
                },
                {
                    "diagnosis": "Acute Gastroenteritis",
                    "symptoms": "Watery diarrhea 4 times, mild dehydration, abdominal cramps",
                    "treatment": "Oral Rehydration Salts (ORS) sachet, Zinc tablets, Probiotics",
                    "temperature": "99.1 °F",
                    "blood_pressure": "110/70 mmHg",
                },
                {
                    "diagnosis": "Malaria (Plasmodium vivax)",
                    "symptoms": "High chills, rigors, intermittent nocturnal fever",
                    "treatment": "Chloroquine course followed by Primaquine under supervision",
                    "temperature": "102.4 °F",
                    "blood_pressure": "118/74 mmHg",
                },
                {
                    "diagnosis": "Bronchial Asthma (Exacerbation)",
                    "symptoms": "Shortness of breath, expiratory wheezing",
                    "treatment": "Salbutamol nebulization, Budesonide inhaler prescribed",
                    "temperature": "98.7 °F",
                    "blood_pressure": "126/82 mmHg",
                },
                {
                    "diagnosis": "Iron Deficiency Anemia",
                    "symptoms": "Fatigue, pallor, brittle nails",
                    "treatment": "Ferrous sulfate 200mg OD + Vitamin C, nutrition advisory",
                    "temperature": "98.5 °F",
                    "blood_pressure": "106/68 mmHg",
                },
            ]

            enc_index = 1
            now = datetime.now(timezone.utc)
            for patient in patient_objects:
                # 1 to 3 encounters per patient
                num_encs = random.randint(1, 3)
                for _ in range(num_encs):
                    enc_code = f"ENC-{enc_index:04d}"
                    enc_case = random.choice(clinical_cases)
                    days_ago = random.randint(0, 60)
                    enc_date = now - timedelta(days=days_ago, hours=random.randint(1, 10))

                    enc = Encounter(
                        encounter_code=enc_code,
                        patient_id=patient.id,
                        clinician_id=clinician_user.id,
                        encounter_date=enc_date,
                        symptoms=enc_case["symptoms"],
                        diagnosis=enc_case["diagnosis"],
                        treatment=enc_case["treatment"],
                        temperature=enc_case["temperature"],
                        blood_pressure=enc_case["blood_pressure"],
                        status=EncounterStatus.COMPLETED.value,
                        notes=(
                            "Scheduled follow-up within 14 days if symptoms persist."
                            if random.random() > 0.5
                            else None
                        ),
                    )
                    db.add(enc)
                    enc_index += 1

            print(f"{enc_index - 1} encounters created.")

        # 4. Audit Log initial entry
        log_entry = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.LOGIN,
            status=AuditStatus.SUCCESS,
            entity_type="SYSTEM",
            entity_id="SEED",
            details="Initial development database seeded successfully",
        )
        db.add(log_entry)

        db.commit()
        print("Seeding completed successfully!")
        print("\nDev Credentials:")
        print("  Admin:     admin@healthtech.local  / HealthTech123!")
        print("  Clinician: doctor@healthtech.local / HealthTech123!")
        print("  Nurse:     nurse@healthtech.local  / HealthTech123!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
