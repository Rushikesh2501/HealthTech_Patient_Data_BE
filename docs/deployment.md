# AWS Deployment & Production Operations Guide

## 1. Cloud Architecture on AWS

The application is deployed as a modular containerized service on AWS.

```
Internet (Clinicians & Remote Centers)
       │
       ▼
AWS Route 53 (DNS)
       │
       ▼
AWS Application Load Balancer (ALB)
  - HTTPS Termination (ACM TLS Certificate)
  - Health checks: GET /health (interval: 30s)
       │
       ▼ (Private VPC Subnet)
AWS ECS on Fargate (FastAPI Container)
  - Tasks running non-root `appuser`
  - Ingests secrets via AWS Secrets Manager
  - Streams logs to Amazon CloudWatch (/ecs/healthtech-backend)
       │
       ▼ (Database Subnet - No Public IP)
Amazon RDS PostgreSQL 16 (Multi-AZ)
```

---

## 2. Infrastructure Primitives

### A. AWS Secrets Manager
Store sensitive parameters under `production/healthtech/backend`:
- `DATABASE_URL`: `postgresql+psycopg://healthtech_app:Pass@rds-endpoint:5432/healthtech`
- `JWT_SECRET_KEY`: High-entropy 64-character secret
- `GEMINI_API_KEY`: API key for Gemini

The backend automatically attempts to read these keys at startup if `AWS_SECRET_NAME` is configured.

### B. Amazon CloudWatch
FastAPI's JSON log formatter outputs structured logs directly to `stdout`. ECS task logging drivers capture these records and route them to CloudWatch Logs:
```json
{
  "timestamp": "2026-10-07T10:15:32.123456Z",
  "level": "INFO",
  "logger": "app.middleware.request_id",
  "message": "POST /api/v1/encounters 201 - 32.40ms",
  "request_id": "8c459bf6-90dc-4f6c-8472-a72a9debaefb",
  "method": "POST",
  "path": "/api/v1/encounters",
  "status_code": 201,
  "duration_ms": 32.40,
  "user_id": 2,
  "client_ip": "10.0.1.42"
}
```

---

## 3. Container Build & CI/CD Pipeline

### 1. Build and Test Image
```bash
docker build -t healthtech-backend:latest .
```

### 2. Push to Amazon ECR
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com

docker tag healthtech-backend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/healthtech-backend:1.0.0
docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/healthtech-backend:1.0.0
```

### 3. Apply Migrations in Production
Before updating the ECS service, run an Alembic migration task:
```bash
aws ecs run-task \
  --cluster healthtech-cluster \
  --task-definition healthtech-migration-task \
  --overrides '{"containerOverrides": [{"name": "migration", "command": ["alembic", "upgrade", "head"]}]}'
```

---

## 4. Troubleshooting & Health Verification

- **Liveness Probe**: `GET http://<host>/health` -> Returns `{"status": "healthy"}`
- **Readiness Probe**: `GET http://<host>/ready` -> Executes `SELECT 1` on PostgreSQL and returns `{"status": "ready", "database": "connected"}`
- **Database Connection Failure**: If RDS is unreachable, `/ready` returns `503 Service Unavailable`, preventing the ALB from directing traffic to unhealthy task instances.
