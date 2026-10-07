# HealthTech Patient Data Dashboard - Backend

A production-grade, secure, testable, and scalable backend for rural healthcare clinics and NGO healthcare networks, built with **Python 3.12+**, **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.x**, and **Google Gemini AI**.

---

## 🏥 Purpose & Architectural Overview

In remote healthcare centers, clinicians and community health workers need to document and review clinical encounters while rigorously safeguarding patient privacy.

Key system capabilities:
- **Anonymized Patient Registry**: Stores zero PII (no names, phone numbers, Aadhaar, emails, or personal addresses). Only sequential codes (`PT-0001`) and clinical demographics.
- **Clinical Encounter Tracking**: Records symptoms, diagnoses, vital signs (blood pressure, temperature), and treatment plans.
- **Permission-Based RBAC**: Strict backend authorization boundaries separating `admin`, `clinician`, and `nurse` roles.
- **PostgreSQL-Powered Analytics**: Real-time aggregated statistics without pulling raw records into application memory.
- **Privacy-Preserving Gemini AI**: Generates epidemiological trend observations by ingesting **only aggregated statistical summaries**. Never receives individual patient data.
- **Immutable Audit Logging**: Captures authentication, CRUD mutations, unauthorized access attempts, and AI requests.
- **AWS Cloud Native**: Engineered for deployment on AWS ECS/Fargate, RDS PostgreSQL, Secrets Manager, and CloudWatch.

```
React Frontend
      │
      │ HTTPS + JWT Bearer
      ▼
AWS Application Load Balancer
      │
      ▼
FastAPI Modular Monolith
      ├── Request ID & Security Headers Middleware
      ├── Centralized Exception & Sanitization Layer
      ├── JWT Authentication & Permission RBAC
      ├── API Layer (Routers)
      ├── Service Layer (Business Logic)
      ├── Repository Layer (Data Access & Postgres Aggregations)
      ├── Audit Logging Service
      └── Privacy-Preserving Gemini AI Service
            │
            ▼
Amazon RDS PostgreSQL (Pooled)
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.12+ |
| **API Framework** | FastAPI (ASGI) |
| **ASGI Server** | Uvicorn |
| **Database** | PostgreSQL 16 (via psycopg 3) |
| **ORM** | SQLAlchemy 2.x |
| **Database Migrations** | Alembic |
| **Data Validation** | Pydantic v2 & Pydantic Settings |
| **Authentication** | JWT (PyJWT) with bcrypt salt hashing |
| **AI Integration** | Google Gemini 1.5 Flash via REST |
| **Testing** | Pytest, HTTPX, FastAPI TestClient |
| **Containerization** | Multi-stage Docker, Docker Compose |
| **Code Quality** | Ruff, Black, MyPy |

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- `uv` (recommended) or `pip` / `virtualenv`
- Docker and Docker Compose (for local PostgreSQL)

### 2. Environment Setup
```bash
# Clone and enter directory
cd PatientManagement_BE

# Copy development environment config
cp .env.example .env.development

# Install dependencies
uv sync
# Or with standard pip:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Start Database & Run Migrations
```bash
# Start local PostgreSQL via Docker Compose
docker compose -f docker-compose.dev.yml up -d db

# Run database migrations
alembic upgrade head

# Seed initial clinical data and development users
python scripts/seed_database.py
```

### 4. Start Development API Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Testing

Execute test suite with pytest:
```bash
pytest tests/ -v
```

Includes:
- **Unit Tests**: Authentication flows, password hashing, RBAC permission matrices, patient & encounter services.
- **Integration Tests**: REST API endpoints, pagination, token validation, audit logging, and RBAC security boundaries.

---

## 📁 Repository Structure

```
PatientManagement_BE/
├── app/
│   ├── api/             # API routers (v1 endpoints for auth, users, patients, encounters, etc.)
│   ├── core/            # Configuration, security, RBAC definitions, logging, exceptions
│   ├── db/              # SQLAlchemy engine, session management, and DeclarativeBase
│   ├── dependencies/    # FastAPI dependency injection (get_db, auth, RBAC permissions)
│   ├── middleware/      # RequestID, structured logging, OWASP security headers
│   ├── models/          # SQLAlchemy ORM models (User, Patient, Encounter, AuditLog)
│   ├── repositories/    # Clean repository pattern with PostgreSQL aggregation queries
│   ├── schemas/         # Pydantic v2 schemas and validation contracts
│   ├── services/        # Domain business logic and Gemini AI integration
│   └── utils/           # Pagination, UTC datetime, and clinical data validators
├── alembic/             # Database migration environments and version scripts
├── docs/                # Architecture, security, API, database, and AWS deployment guides
├── scripts/             # Admin generator and database seeding scripts
├── tests/               # Unit and integration tests with pytest and HTTPX
├── Dockerfile           # Multi-stage production container image
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── pyproject.toml
├── alembic.ini
├── Makefile
└── README.md
```

---

## 🔒 Security Principles

1. **Backend as Source of Truth**: Frontend permission checks only customize UI layout. The backend dependencies enforce HTTP 401/403 boundaries.
2. **Strict Anonymization**: No patient PII is accepted or stored in the database.
3. **AI Sanitization Barrier**: Google Gemini never receives individual records or patient IDs; only pre-aggregated PostgreSQL statistics are shared.
4. **Credential Isolation**: Secrets are never hardcoded. In AWS, secrets are retrieved dynamically via AWS Secrets Manager or secure IAM task roles.
