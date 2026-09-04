class SpamDetected(Exception):
    """Raised when a submission is judged to be spam."""


def check_honeypot(hp_field: str | None) -> None:
    """
    The widget config ships a hidden `hp_field` input that real visitors never see
    (styled off-screen / display:none) and therefore never fill.
    A bot filling every field in the DOM will fill it. Any non-empty value = spam.
    We reject silently to the bot (a generic 4xx) without revealing why, so the
    bot can't learn to leave it blank.
    """
    if hp_field:
        raise SpamDetected("honeypot field was filled")
