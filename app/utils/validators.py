"""Common domain validation helpers."""

import re
from typing import Optional


def validate_anonymized_patient_code(code: str) -> bool:
    """Validate format PT-XXXX (e.g. PT-0001, PT-9999)."""
    return bool(re.match(r"^PT-\d{4,}$", code.strip()))


def validate_blood_pressure_format(bp: Optional[str]) -> bool:
    """Validate standard clinical blood pressure string (e.g. 120/80 or 120/80 mmHg)."""
    if not bp:
        return True
    return bool(re.match(r"^\d{2,3}/\d{2,3}(\s*mmHg)?$", bp.strip(), re.IGNORECASE))


def validate_temperature_format(temp: Optional[str]) -> bool:
    """Validate temperature value (e.g. 98.6, 98.6 °F, 37.0 C)."""
    if not temp:
        return True
    return bool(re.match(r"^\d{2,3}(\.\d)?\s*(°?[FCfc])?$", temp.strip()))
