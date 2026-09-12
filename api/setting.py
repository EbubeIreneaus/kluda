from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str = "retail-pos-super-secret-jwt-key-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 13

    DOMAIN_NAME: str = "localhost"
    APP_ENV: str = "development"

    REDIS_URL: str = "redis://localhost:6379"

    VAPID_PUBLIC_KEY: str
    VAPID_PRIVATE_KEY: str
    VAPID_CLAIM_EMAIL: str

    DEFAULT_RATE_LIMIT: str = "120/minute"
    AUTH_RATE_LIMIT: str = "10/minute"

    SUPER_STAFF_EMAIL: str = "admin@example.com"
    SUPER_STAFF_NAME: str = "Admin"
    SUPER_STAFF_PASSWORD: str = "Admin@123456"

    RESEND_API_KEY: str
    RESEND_SIGNING_SECRET: str

    CLOUDINARY_NAME: str
    CLOUDINARY_SECRET: str
    CLOUDINARY_KEY: str
    IMAGE_FOLDER: str = "kluda"

    SUPER_ADMIN_NAME: str
    SUPER_ADMIN_EMAIL: str
    SUPER_ADMIN_PASSWORD: str
    SUPER_ADMIN_PHONE: str

    PAYSTACK_SECRET: str
    PAYSTACK_PUBLIC: str

    DEMO_ACCOUNT_EMAILS: str = "demo@kluda.com,pitch@kluda.com,demo@example.com,admin@example.com"

    @property
    def demo_emails_list(self) -> list[str]:
        return [e.strip().lower() for e in self.DEMO_ACCOUNT_EMAILS.split(",") if e.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()