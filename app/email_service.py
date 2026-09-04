import logging

import httpx

from app.config import settings

logger = logging.getLogger("email_side_effect")


def send_confirmation(submission_id: str, widget_title: str, data: dict) -> str:
    """
    Fires a confirmation email/webhook for a new submission.
    Contract: this function's caller MUST treat any exception here as non-fatal.
    Returns one of "sent" | "failed" — never raises past this boundary in production
    use (see routers/public.py, which wraps the call in try/except anyway as a
    second line of defense).
    """
    try:
        if settings.email_side_effect_force_fail:
            raise RuntimeError("forced failure (EMAIL_SIDE_EFFECT_FORCE_FAIL=true)")

        if settings.email_side_effect_mode == "webhook" and settings.email_webhook_url:
            httpx.post(
                settings.email_webhook_url,
                json={"submission_id": submission_id, "widget_title": widget_title, "data": data},
                timeout=2.0,
            ).raise_for_status()
        else:
            logger.info(
                "[console email] New submission %s for widget '%s': %s",
                submission_id, widget_title, data,
            )
        return "sent"
    except Exception as exc:  # noqa: BLE001 — side effects must degrade, never propagate
        logger.warning("confirmation side-effect failed for submission %s: %s", submission_id, exc)
        return "failed"
