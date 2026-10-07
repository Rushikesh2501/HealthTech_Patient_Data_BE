# Security Architecture & Compliance

## 1. Core Security Principles

The backend is built according to defense-in-depth and least-privilege standards:
- **Backend as Security Boundary**: Client-side visibility controls are purely UX. All security decisions and permissions are evaluated on the server.
- **Anonymization by Design**: The schema completely excludes personally identifiable information (PII) such as patient names, phone numbers, email addresses, national IDs (e.g. Aadhaar), or physical addresses.
- **Auditing Everything**: All logins, authentication failures, CRUD operations, unauthorized access attempts, and AI queries produce immutable audit logs.
- **Secret Isolation**: Secrets are separated from source code and managed via AWS Secrets Manager in production.

---

## 2. Authentication & JWT Token Architecture

### Token Types & Lifecycles
1. **Access Token**: Short-lived JWT (30 minutes default) signed with HMAC-SHA256. Contains minimal claims:
   ```json
   {
     "sub": "42",
     "role": "clinician",
     "type": "access",
     "iat": 1791350000,
     "exp": 1791351800
   }
   ```
   *Note: Never contains patient information or passwords.*
2. **Refresh Token**: Long-lived JWT (7 days default) with `"type": "refresh"`. Exchanged via `POST /api/v1/auth/refresh` to rotate tokens without requiring re-authentication.

### Password Hashing
- Handled with **bcrypt** using unique per-user 12-round salt hashing.
- Plaintext passwords are never logged, cached, or returned in API responses.

---

## 3. Role-Based Access Control (RBAC)

The system defines 3 primary roles with fine-grained permission bindings:

| Permission | Admin | Clinician | Nurse |
|---|:---:|:---:|:---:|
| `patients.read` | ✅ | ✅ | ✅ |
| `patients.create` | ✅ | ✅ | ❌ |
| `patients.update` | ✅ | ✅ | ❌ |
| `patients.delete` | ✅ | ❌ | ❌ |
| `encounters.read` | ✅ | ✅ | ✅ |
| `encounters.create` | ✅ | ✅ | ✅ |
| `encounters.update` | ✅ | ✅ | ✅ |
| `encounters.delete` | ✅ | ❌ | ❌ |
| `analytics.read` | ✅ | ✅ | ❌ |
| `analytics.ai.read` | ✅ | ✅ | ❌ |
| `audit.read` | ✅ | ❌ | ❌ |
| `users.*` | ✅ | ❌ | ❌ |
| `settings.manage` | ✅ | ❌ | ❌ |

### Enforcement Pattern
```python
@router.delete(
    "/{patient_id}",
    dependencies=[Depends(require_permission("patients.delete"))]
)
def delete_patient(patient_id: int, ...):
    ...
```
If a clinician or nurse sends a `DELETE` request, the backend immediately halts execution, logs an `UNAUTHORIZED_ACCESS` audit event, and returns:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN_PERMISSION",
    "message": "Access denied. You do not have permission 'patients.delete'.",
    "details": {
      "required_permission": "patients.delete",
      "user_role": "clinician"
    }
  },
  "request_id": "8f8b5f92-5629-450a-9d93-c40d6c54784a"
}
```

---

## 4. AWS IAM vs. Application RBAC Separation

A fundamental rule of this architecture is the clean separation of infrastructure and application permissions:

```
┌───────────────────────────────────┐
│        AWS IAM Layer              │
│  Controls AWS Infrastructure:     │
│  - ECS Task Execution Role        │
│  - Amazon RDS Access              │
│  - AWS Secrets Manager Read       │
│  - Amazon CloudWatch Log Writes   │
└─────────────────┬─────────────────┘
                  │
                  ▼
┌───────────────────────────────────┐
│     FastAPI Application RBAC      │
│  Controls Domain Access:          │
│  - Clinician encounter entry      │
│  - Nurse encounter view           │
│  - Admin staff management         │
│  - AI trend analysis access       │
└───────────────────────────────────┘
```
**Never conflate the two**: AWS IAM is not used to check if a doctor can write a prescription. Application RBAC is handled entirely within FastAPI.

---

## 5. Network & HTTP Hardening

- **CORS**: Explicitly restricted to authorized frontend domains (e.g. `http://localhost:3000` or production CDN). Wildcard `*` origins are rejected.
- **OWASP Headers**: Every response includes:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Strict-Transport-Security: max-age=31536000` (in production)
- **Input Sanitization**: Pydantic v2 rejects malformed payloads before business logic execution.
- **Centralized Error Sanitizer**: Database connection errors and stack traces are suppressed in HTTP responses and logged to internal loggers with request IDs.
