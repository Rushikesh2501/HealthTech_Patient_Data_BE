# API Documentation & Endpoint Reference

Base URL prefix: `/api/v1` (with `/api` compatibility aliases).

All protected endpoints require an `Authorization: Bearer <token>` header.

---

## 1. Authentication (`/api/v1/auth`)

### `POST /api/v1/auth/login`
- **Description**: Authenticate user credentials and issue JWT tokens.
- **Payload**:
  ```json
  {
    "email": "doctor@healthtech.local",
    "password": "HealthTech123!",
    "rememberMe": true
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "bearer",
    "token": "eyJhbG...",
    "expires_in": 1800,
    "user": {
      "id": 2,
      "email": "doctor@healthtech.local",
      "name": "Dr. Rajesh Sharma",
      "role": "clinician",
      "is_active": true,
      "last_login_at": "2026-10-07T10:00:00Z",
      "created_at": "2026-10-07T08:00:00Z",
      "updated_at": "2026-10-07T10:00:00Z"
    }
  }
  ```

### `POST /api/v1/auth/refresh`
- **Description**: Issue a new token pair from an existing valid refresh token.
- **Payload**:
  ```json
  {
    "refreshToken": "eyJhbG..."
  }
  ```

### `POST /api/v1/auth/logout`
- **Description**: Logs out user and writes a `LOGOUT` audit trail.

### `GET /api/v1/auth/me`
- **Description**: Returns profile details for the authenticated bearer token.

---

## 2. Patients (`/api/v1/patients`)

### `GET /api/v1/patients`
- **Permissions**: `patients.read`
- **Query Parameters**:
  - `page` (int, default: 1)
  - `pageSize` (int, default: 20, max: 100)
  - `search` (string, searches patient code e.g. `PT-0001`)
  - `gender` (`Male`, `Female`, `Other`)
  - `ageMin`, `ageMax` (integers)
  - `status` (`active`, `inactive`)
  - `dateFrom`, `dateTo` (dates, `YYYY-MM-DD`)
- **Response `200 OK`**:
  ```json
  {
    "data": [
      {
        "id": 1,
        "patientId": "PT-0001",
        "age": 42,
        "gender": "Female",
        "registrationDate": "2026-08-10",
        "status": "active",
        "totalEncounters": 3,
        "lastEncounterDate": "2026-10-05T09:30:00Z",
        "created_at": "2026-08-10T08:00:00Z",
        "updated_at": "2026-08-10T08:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 25,
      "totalPages": 2
    }
  }
  ```

### `POST /api/v1/patients`
- **Permissions**: `patients.create`
- **Payload**:
  ```json
  {
    "age": 28,
    "gender": "Male",
    "status": "active"
  }
  ```

### `GET /api/v1/patients/{id}`
- **Permissions**: `patients.read`

### `PATCH /api/v1/patients/{id}`
- **Permissions**: `patients.update`

### `DELETE /api/v1/patients/{id}`
- **Permissions**: `patients.delete` (Admin only)

---

## 3. Encounters (`/api/v1/encounters`)

### `GET /api/v1/encounters`
- **Permissions**: `encounters.read`
- **Query Parameters**: `search`, `patientId`, `clinicianId`, `diagnosis`, `status`, `dateFrom`, `dateTo`, `page`, `pageSize`.

### `POST /api/v1/encounters`
- **Permissions**: `encounters.create`
- **Payload**:
  ```json
  {
    "patientId": 1,
    "symptoms": "Fever, dry cough for 3 days",
    "diagnosis": "Upper Respiratory Tract Infection",
    "treatment": "Amoxicillin 500mg, Paracetamol 650mg",
    "temperature": "100.4 °F",
    "bloodPressure": "120/80 mmHg",
    "status": "completed",
    "notes": "Advised hydration and rest"
  }
  ```

### `GET /api/v1/encounters/{id}`
- **Permissions**: `encounters.read`

### `PATCH /api/v1/encounters/{id}`
- **Permissions**: `encounters.update`

### `DELETE /api/v1/encounters/{id}`
- **Permissions**: `encounters.delete` (Admin only)

---

## 4. Dashboard & Analytics (`/api/v1/dashboard`, `/api/v1/analytics`)

### `GET /api/v1/dashboard/summary`
- **Permissions**: `analytics.read`
- **Response**:
  ```json
  {
    "totalPatients": 25,
    "totalEncounters": 54,
    "encountersToday": 3,
    "activeClinicians": 2,
    "patientsChangePercentage": 8.5,
    "encountersChangePercentage": 12.0,
    "todayChangePercentage": 5.2
  }
  ```

### `GET /api/v1/dashboard/trends`
- Returns time-series daily encounter volume and follow-up visit counts.

### `GET /api/v1/dashboard/diagnoses`
- Returns diagnosis frequency and percentages calculated via PostgreSQL aggregation.

### `GET /api/v1/dashboard/age-distribution`
- Returns patient counts grouped by age bracket (`0-18`, `19-35`, `36-50`, `51-65`, `65+`) and gender.

---

## 5. Gemini AI Trend Analysis (`/api/v1/ai`)

### `POST /api/v1/ai/trends`
- **Permissions**: `analytics.ai.read` (Clinician & Admin; Nurses return 403 Forbidden).
- **Payload**:
  ```json
  {
    "question": "What is driving the recent increase in respiratory cases?",
    "from_date": "2026-09-01",
    "to_date": "2026-10-01"
  }
  ```
- **Response**:
  ```json
  {
    "summary": "Respiratory infections accounted for 42% of total encounters during this period.",
    "observations": [
      "Visits clustered during transition into post-monsoon climate conditions.",
      "Pediatric and geriatric age brackets represent 65% of recorded respiratory symptoms.",
      "Antibiotic treatments remained consistent with local clinical protocols."
    ],
    "limitations": [
      "Correlation with weather patterns does not prove causal etiology without environmental sampling.",
      "Walk-in visits without prior clinic history may introduce reporting delay."
    ],
    "data_points_analyzed": 54,
    "generated_at": "2026-10-07T10:15:00Z"
  }
  ```

---

## 6. Audit Logs (`/api/v1/audit-logs`)

### `GET /api/v1/audit-logs`
- **Permissions**: `audit.read` (Admin only)
- **Query Parameters**: `action`, `userId`, `status`, `dateFrom`, `dateTo`, `page`, `pageSize`.
