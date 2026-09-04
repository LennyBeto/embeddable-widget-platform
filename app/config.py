from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://widget_user:widget_pass@db:5432/widget_platform"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    redis_url: str = "redis://localhost:6379/0"

    geo_provider_a_url: str = "http://ip-api.com/json"
    geo_provider_b_url: str = "https://ipapi.co"
    geo_provider_a_force_down: bool = False
    geo_provider_b_force_down: bool = False

    email_side_effect_mode: str = "console"  # "console" | "webhook"
    email_webhook_url: str = ""
    email_side_effect_force_fail: bool = False

    allowed_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    rate_limit_per_ip: str = "10/minute"
    rate_limit_per_widget: str = "30/minute"

    widget_bundle_version: str = "v1"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
