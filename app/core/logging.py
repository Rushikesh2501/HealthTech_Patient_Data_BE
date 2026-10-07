"""Structured logging setup for production and CloudWatch compatibility."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formats log records into JSON for CloudWatch and modern log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include request_id if attached
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Include extra audit or diagnostic fields
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            # Sanitize any accidental sensitive keys
            sanitized = {
                k: v
                for k, v in record.extra_fields.items()
                if k.lower() not in {"password", "token", "secret", "authorization", "key"}
            }
            log_entry.update(sanitized)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", app_env: str = "development") -> None:
    """Configure root logger with either structured JSON or standard color format."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if app_env.lower() == "production":
        handler.setFormatter(JSONFormatter())
    else:
        standard_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(standard_formatter)

    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
