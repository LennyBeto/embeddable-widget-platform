# Build Log — AI usage

## Where AI helped
- Scaffolded the initial FastAPI project layout (routers, models, schemas) from the
  capstone brief's architecture section.
- Drafted the provider-fallback pattern in `app/geo.py` and the "never fail the main
  path" pattern in `app/email_service.py`.
- Drafted the vanilla-JS widget loader in `static/widget.v1.js`.

## Where it was wrong / needed correction
- the first draft of the rate limiter didn't stack a per-widget limit alongside the per-IP one; had to add a second Limiter instance
- generated Alembic setup was skipped in favor of `Base.metadata.create_all`
  for the capstone's time budget — note this as a known limitation in the README">

## What I changed
- `requirements.txt` — pinned `bcrypt==4.0.1` after passlib's bcrypt backend threw
  `AttributeError: module 'bcrypt' has no attribute '__about__'` against the latest
  bcrypt release; also added `email-validator`, which `pydantic.EmailStr` needs at
  runtime but doesn't pull in on its own.
- `app/main.py` — the custom `RequestValidationError` handler was returning
  `exc.errors()` straight into `JSONResponse`, which broke with
  `TypeError: Object of type ValueError is not JSON serializable` whenever a custom
  Pydantic `field_validator` raised (e.g. the oversized-payload check in
  `schemas.py`). Fixed by stripping the non-serializable `ctx` key and running the
  rest through `jsonable_encoder` before returning it.
- `app/routers/public.py` — `get_widget_bundle` was setting the `Cache-Control`
  header on an injected `Response` object but returning a separate `FileResponse`,
  so the header was silently dropped (verified with `curl -I`, saw no
  `cache-control` in the reply). Fixed by building the `FileResponse` first and
  setting the header on that instance directly.
- `seed.py` — the demo email used `owner@acme.test`; `.test` is an RFC 2606 reserved
  TLD and `email-validator` rejects it, so seeding failed with a 422 the first time
  I ran it against a live server. Switched to `owner@acme-demo.com`.
- `docker-compose.yml` / `.env.example` — originally had the Postgres user/password
  hardcoded in `docker-compose.yml` and duplicated inside `DATABASE_URL` in `.env`,
  which is easy to let drift out of sync. Changed the `db` service to read
  `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`, `${POSTGRES_DB}` from `.env` so there's
  one place to update credentials (still have to keep the password inside
  `DATABASE_URL` matching manually — noted as a limitation, not fully solved).

## Code I can explain line-by-line if asked
- The honeypot + rate-limit + geo-fallback + safe-side-effect pipeline in
  `app/routers/public.py::submit_widget_form` — this is the core of the capstone.
- The tenant-isolation choke point in `app/routers/widgets.py::_get_owned_widget_or_404`.
