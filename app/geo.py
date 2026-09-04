import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger("geo")


@dataclass
class GeoResult:
    country: str | None
    city: str | None
    provider: str | None  # "provider_a" | "provider_b" | None if all failed


def _query_provider_a(ip: str) -> GeoResult | None:
    if settings.geo_provider_a_force_down:
        return None
    try:
        resp = httpx.get(f"{settings.geo_provider_a_url}/{ip}", timeout=2.0)
        resp.raise_for_status()
        body = resp.json()
        if body.get("status") == "fail":
            return None
        return GeoResult(country=body.get("country"), city=body.get("city"), provider="provider_a")
    except Exception as exc:  # noqa: BLE001 — any upstream failure just means "try the fallback"
        logger.warning("geo provider A failed: %s", exc)
        return None


def _query_provider_b(ip: str) -> GeoResult | None:
    if settings.geo_provider_b_force_down:
        return None
    try:
        resp = httpx.get(f"{settings.geo_provider_b_url}/{ip}/json/", timeout=2.0)
        resp.raise_for_status()
        body = resp.json()
        if body.get("error"):
            return None
        return GeoResult(country=body.get("country_name"), city=body.get("city"), provider="provider_b")
    except Exception as exc:  # noqa: BLE001
        logger.warning("geo provider B failed: %s", exc)
        return None


def enrich_ip(ip: str) -> GeoResult:
    """
    Provider A -> Provider B -> give up gracefully.
    A submission NEVER fails because enrichment failed — this always returns
    a GeoResult, with provider=None and blank fields when every upstream is down.
    """
    if not ip or ip in ("testclient", "unknown", "127.0.0.1"):
        # Local/dev traffic has no meaningful public geo — skip the network calls.
        result = _query_provider_a(ip) if not settings.geo_provider_a_force_down else None
        if result:
            return result
        return GeoResult(country=None, city=None, provider=None)

    result = _query_provider_a(ip)
    if result:
        return result

    result = _query_provider_b(ip)
    if result:
        return result

    logger.warning("all geo providers down for ip=%s — storing submission without geo data", ip)
    return GeoResult(country=None, city=None, provider=None)
