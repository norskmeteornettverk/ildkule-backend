import logging
from typing import Any

import requests

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def verify_recaptcha(token: str) -> bool:
    """Validate Google reCAPTCHA token when a secret is configured."""
    if not settings.recaptcha_secret:
        logger.debug("reCAPTCHA secret missing; skipping verification")
        return True

    try:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": settings.recaptcha_secret, "response": token},
            timeout=8,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Could not reach Google reCAPTCHA")
        return False

    payload: dict[str, Any] = response.json()
    return bool(payload.get("success"))

