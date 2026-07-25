"""
Structured logging for PatentPilot.
Every pipeline stage emits a structured log entry.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Emit logs as JSON for structured logging pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger with structured JSON output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_pipeline_stage(logger: logging.Logger, stage: str, data: dict[str, Any]):
    """Emit a structured pipeline stage log."""
    extra_data = data.copy()
    extra_data.pop("message", None)
    logger.info(
        f"[PIPELINE:{stage}] {data.get('message', '')}",
        extra={"stage": stage, **extra_data}
    )
