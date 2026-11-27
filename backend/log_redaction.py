import logging
import os
import re

REDACTED = "[REDACTED]"

_SECRET_QUERY_PARAM = re.compile(
    r"(?i)\b(app_id|app_key|api_key|apikey|key|token|access_token|secret|password)=([^&\s'\"#]+)"
)

_SECRET_ENV_VARS = (
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "REED_API_KEY",
    "RAPIDAPI_KEY",
    "ANTHROPIC_API_KEY",
    "SECRET_KEY",
    "GOOGLE_CLIENT_SECRET",
)
# Shorter values are CI placeholders like "ci"; masking them would mangle ordinary words in log lines.
_MIN_SECRET_LENGTH = 6


def redact_secrets(text: str) -> str:
    text = _SECRET_QUERY_PARAM.sub(lambda m: f"{m.group(1)}={REDACTED}", text)
    for name in _SECRET_ENV_VARS:
        value = (os.getenv(name) or "").strip()
        if len(value) >= _MIN_SECRET_LENGTH:
            text = text.replace(value, REDACTED)
    return text


class RedactSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = redact_secrets(message)
        if redacted != message:
            record.msg = redacted
            record.args = None
        return True


def install_secret_redaction(*logger_names: str) -> None:
    for name in logger_names:
        logger = logging.getLogger(name)
        if not any(isinstance(f, RedactSecretsFilter) for f in logger.filters):
            logger.addFilter(RedactSecretsFilter())
