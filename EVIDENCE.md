# Evidence

One proof per checkbox in Section 6 of the capstone brief. Fill in the `$ command` and
paste real output as you complete each step — don't ship this file with placeholders.

## Widget management

- [ ] **Authenticated CRUD; unauthenticated requests rejected**
  ```
  $ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/widgets
  401
  ```

- [ ] **Multi-tenant isolation proven**
  ```
  $ pytest tests/test_submission.py::test_tenant_isolation_on_widget_routes -v
  <paste output — should PASS, confirming tenant B gets a 404 on tenant A's widget>
  ```

## Widget delivery

- [ ] **Embed snippet generated per widget** — paste a `POST /widgets` response showing `embed_snippet`.
- [ ] **Public config endpoint serves correct Cache-Control**
  ```
  $ curl -sI http://localhost:8000/widgets/<id>/config | grep -i cache-control
  cache-control: public, max-age=60
  ```
- [ ] **Widget JS served as a versioned bundle**
  ```
  $ curl -sI http://localhost:8000/widget/v1/widget.js | grep -i cache-control
  cache-control: public, max-age=31536000, immutable
  ```
- [ ] **Widget renders on a page from a different origin** — screenshot or note: served
  `customer-site/index.html` via `python -m http.server 5500` (origin `http://localhost:5500`)
  against the API on `http://localhost:8000`; widget rendered and submitted successfully.

## Public submission API

- [ ] **Cross-origin submissions work (CORS + preflight)**
  ```
  $ curl -s -X OPTIONS http://localhost:8000/widgets/<id>/submissions \
      -H "Origin: http://localhost:5500" \
      -H "Access-Control-Request-Method: POST" -i | grep -i access-control
  ```
- [ ] **Malformed/oversized payloads rejected with 4xx JSON**
  ```
  $ pytest tests/test_submission.py::test_missing_required_field_returns_422 \
           tests/test_submission.py::test_oversized_payload_returns_422 -v
  ```
- [ ] **Valid submissions stored, linked to widget + tenant**
  ```
  $ pytest tests/test_submission.py::test_valid_submission_is_stored -v
  ```

## Abuse protection

- [ ] **Rate limiting returns 429 under burst, legitimate traffic still served after**
  ```
  $ for i in $(seq 1 15); do curl -s -o /dev/null -w "%{http_code} " \
      -X POST http://localhost:8000/widgets/<id>/submissions \
      -H "Content-Type: application/json" -d '{"data":{"email":"a@a.com"},"hp_field":""}'; done
  <paste the run of status codes — expect 201s then 429s, then a 201 again after the window resets>
  ```
- [ ] **Honeypot demonstrably blocks a spam submission**
  ```
  $ pytest tests/test_submission.py::test_honeypot_filled_rejects_submission -v
  ```

## Enrichment & safe side effects

- [ ] **Provider fallback chain: A down -> B answers**
  ```
  $ # set GEO_PROVIDER_A_FORCE_DOWN=true in .env, restart, then submit a form
  $ curl -s http://localhost:8000/dashboard/submissions -H "Authorization: Bearer <token>" | jq '.[0].geo_provider'
  "provider_b"
  ```
- [ ] **All providers down -> submission still succeeds, no geo data**
  ```
  $ # set GEO_PROVIDER_A_FORCE_DOWN=true and GEO_PROVIDER_B_FORCE_DOWN=true, restart, submit
  <paste 201 response showing "geo_provider": null>
  ```
- [ ] **Failing confirmation side effect does not block the submission**
  ```
  $ # set EMAIL_SIDE_EFFECT_FORCE_FAIL=true in .env, restart, submit
  <paste 201 response showing "email_side_effect_status": "failed">
  ```

## Documentation

- [ ] README with architecture diagram, setup, and API docs — see `README.md`.
- [ ] `capstone.yaml`, `BUILDLOG.md`, `.env.example` present at repo root.
