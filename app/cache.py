from fastapi import Response

# Widget JS bundle is versioned in its URL (e.g. /widget/v1/widget.js) so it can be
# cached "forever" — a new release ships under a new version path instead of
# invalidating this one.
BUNDLE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year, immutable

# Widget config can change any time the owner edits the widget, so it gets a
# short-lived cache instead.
CONFIG_MAX_AGE = 60  # 1 minute


def set_bundle_cache_headers(response: Response) -> None:
    response.headers["Cache-Control"] = f"public, max-age={BUNDLE_MAX_AGE}, immutable"


def set_config_cache_headers(response: Response) -> None:
    response.headers["Cache-Control"] = f"public, max-age={CONFIG_MAX_AGE}"
