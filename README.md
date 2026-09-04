# Embeddable Widget & Lead-Capture Platform

FlyRank Internship · Backend Track · Capstone (Python / FastAPI lane)

A platform that lets a customer configure an embeddable widget (signup form / CTA
popover), hand out a one-line `<script>` tag, and safely catch whatever the public
internet sends back — validated, spam-filtered, geo-enriched, and dashboarded.

## Architecture

```
Widget Owner (authenticated, JWT)
   │
   ├─ POST/GET/PATCH/DELETE /widgets          Widget Management API
   │                                          (tenant-isolated CRUD)
   │
   └─ GET /dashboard/stats, /dashboard/submissions   Owner Dashboard API

Customer Website (any origin — e.g. http://localhost:5500)
   │  <script src="http://localhost:8000/widget/v1/widget.js?id=abc123">
   │
   ├─ GET /widget/v1/widget.js                 versioned bundle, cached 1 year
   └─ GET /widgets/{id}/config                 public config, cached 60s (CORS)

Website Visitor (the entire internet)
   │
   └─ POST /widgets/{id}/submissions           public, CORS-enabled
        │
        ├─ 1. widget must exist + be active ───────────────► 404
        ├─ 2. payload validated by Pydantic ────────────────► 422 (never 500)
        ├─ 3. honeypot check ────────────────────────────────► 400 if bot
        ├─ 4. rate limit (per-IP AND per-widget) ────────────► 429 under burst
        ├─ 5. geo enrichment: Provider A → Provider B → skip  (never fails)
        ├─ 6. store submission (tenant + widget linked)
        └─ 7. safe side effect: confirmation email/webhook   (never fails the response)
```

Three request paths, three trust levels: the owner is authenticated and trusted with
their own tenant's data only; the customer site is untrusted but expected traffic
(hence CORS, not auth); the visitor is the open internet and is trusted with nothing —
every input is validated, rate-limited, and spam-checked before it touches storage.

## Stack

- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL (via Docker Compose); SQLAlchemy ORM
- **Rate limiting:** Redis + `slowapi`
- **Auth:** JWT (`python-jose`) + bcrypt password hashing (`passlib`)
- **Geo enrichment:** [ip-api.com](https://ip-api.com) (provider A) →
  [ipapi.co](https://ipapi.co) (provider B), both free, no API key
- **Everything else:** `httpx` for outbound calls, plain vanilla JS for the widget bundle

## Setup — run on a clean machine

```bash
git clone https://github.com/LennyBeto/embeddable-widget-platform
cd embeddable-widget-platform
cp .env.example .env          # defaults work out of the box for local dev
docker compose up --build     # starts api (FastAPI), db (Postgres), redis
```

The API is now live at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

**Seed demo data** (one tenant, one login, one ready-to-embed widget):

```bash
docker compose exec api python seed.py
```

This prints a demo login (`owner@acme-demo.com` / `demo-password-123`) and a widget id.
Paste the printed `<script>` tag into `customer-site/index.html` (replacing
`REPLACE_WITH_WIDGET_ID`), then serve that folder from a **different port** to prove
the cross-origin path:

```bash
cd customer-site
python -m http.server 5500
# open http://localhost:5500 in a browser — the widget renders and submits
# across origins to the API on :8000
```

**Run tests:**

```bash
docker compose exec api pytest -v
```

## API reference

### Auth

| Method | Path            | Auth | Notes                                   |
|--------|-----------------|------|------------------------------------------|
| POST   | `/auth/signup`  | none | Creates a tenant + owner user, returns a JWT |
| POST   | `/auth/login`   | none | OAuth2 password form (`username`=email), returns a JWT |

### Widget management (authenticated — `Authorization: Bearer <token>`)

| Method | Path                    | Notes |
|--------|-------------------------|-------|
| POST   | `/widgets`               | Create a widget; returns it with a ready-to-paste `embed_snippet` |
| GET    | `/widgets`               | List the caller's own tenant's widgets only |
| GET    | `/widgets/{id}`          | 404 if the widget belongs to another tenant |
| PATCH  | `/widgets/{id}`          | Partial update (title, fields, active flag, ...) |
| DELETE | `/widgets/{id}`          | 204 on success |

### Public, cached delivery (no auth)

| Method | Path                          | Cache-Control                         |
|--------|-------------------------------|----------------------------------------|
| GET    | `/widget/v1/widget.js`        | `public, max-age=31536000, immutable`  |
| GET    | `/widgets/{id}/config`        | `public, max-age=60`                   |

### Public submission (no auth, CORS-enabled)

| Method | Path                              | Notes |
|--------|-----------------------------------|-------|
| POST   | `/widgets/{id}/submissions`       | Body: `{"data": {...}, "hp_field": ""}`. See pipeline above. |

### Dashboard (authenticated)

| Method | Path                     | Notes |
|--------|--------------------------|-------|
| GET    | `/dashboard/submissions` | Optional `?widget_id=` filter |
| GET    | `/dashboard/stats`       | Totals, per-widget, per-country, last-7-days counts |

## Design decisions & non-goals

- **Non-goal:** no real hosting/CDN/domain. The "customer site" is a plain HTML file
  on a second local port, exactly as the brief's realistic-scope section allows.
- **Non-goal:** no form-builder UI. One widget type (`signup_form`) is exercised
  end-to-end; the data model supports `cta_popover` too, but it isn't built out —
  the point of this capstone is the hardened public API, not a form-builder startup.
- **Migrations:** `Base.metadata.create_all` is used for simplicity within the time
  budget instead of a full Alembic migration history. Alembic is included in
  `requirements.txt` for anyone extending this into production.
- **Rate limiting** stacks two independent `slowapi` limiters on the submission route:
  one keyed by client IP, one keyed by widget id — so a burst against one widget
  can't silently fall under a shared bucket with traffic to another.
- **Geo enrichment and the confirmation side effect are both allowed to fail** —
  the submission's HTTP response never depends on either succeeding. This is
  enforced at two levels: `geo.enrich_ip` and `email_service.send_confirmation`
  swallow their own exceptions internally, and the caller in
  `routers/public.py` wraps the side-effect call in `try/except` again anyway.

## Limitations

- No production-grade CAPTCHA/proof-of-work bot defense — only a honeypot field
  (sufficient per the brief's "at least one spam-prevention technique" requirement).
- Rate-limit windows use `slowapi`'s in-memory-per-process view of Redis counters;
  fine for a single API instance, would need sticky config review for a multi-node
  deploy.
- No frontend build step for the widget — it's hand-written vanilla JS, matching
  the brief's "backend capstone, not a frontend one" framing.
