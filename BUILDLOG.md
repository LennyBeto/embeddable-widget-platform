# Build Log — AI usage

Honesty is graded here, not perfection. Keep entries short and specific.

## Where AI helped
- Scaffolded the initial FastAPI project layout (routers, models, schemas) from the
  capstone brief's architecture section.
- Drafted the provider-fallback pattern in `app/geo.py` and the "never fail the main
  path" pattern in `app/email_service.py`.
- Drafted the vanilla-JS widget loader in `static/widget.v1.js`.

## Where it was wrong / needed correction
- <fill in as you build — e.g. "the first draft of the rate limiter didn't stack a
  per-widget limit alongside the per-IP one; had to add a second Limiter instance">
- <e.g. "generated Alembic setup was skipped in favor of `Base.metadata.create_all`
  for the capstone's time budget — note this as a known limitation in the README">

## What I changed
- <fill in as you build — be specific: files touched, why, what you understood
  about the resulting code>

## Code I can explain line-by-line if asked
- The honeypot + rate-limit + geo-fallback + safe-side-effect pipeline in
  `app/routers/public.py::submit_widget_form` — this is the core of the capstone.
- The tenant-isolation choke point in `app/routers/widgets.py::_get_owned_widget_or_404`.
