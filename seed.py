"""
Seed step referenced in capstone.yaml and the README.
Creates one demo tenant, one owner login, and one ready-to-embed widget.

Run inside the api container (or locally with DATABASE_URL pointed at Postgres):
    docker compose exec api python seed.py
"""
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Tenant, User, Widget, WidgetType

Base.metadata.create_all(bind=engine)
db = SessionLocal()

DEMO_EMAIL = "owner@acme-demo.com"
DEMO_PASSWORD = "demo-password-123"

existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
if existing:
    print(f"Demo user already exists: {DEMO_EMAIL}")
else:
    tenant = Tenant(name="Acme Co.")
    db.add(tenant)
    db.flush()

    user = User(tenant_id=tenant.id, email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD))
    db.add(user)

    widget = Widget(
        tenant_id=tenant.id,
        type=WidgetType.signup_form,
        title="Join our newsletter",
        description="Get product updates, no spam.",
        fields=[{"name": "email", "label": "Email address", "field_type": "email", "required": True}],
        button_text="Subscribe",
        display_options={"theme": "light"},
    )
    db.add(widget)
    db.commit()

    print("Seed complete.")
    print(f"  Login:      {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Widget id:  {widget.id}")
    print(f"  Embed:      <script src=\"http://localhost:8000/widget/v1/widget.js?id={widget.id}\"></script>")

db.close()
