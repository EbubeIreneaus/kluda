from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str = "retail-pos-super-secret-jwt-key-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 13

    SUPER_STAFF_NAME: str 
    SUPER_STAFF_EMAIL: str
    SUPER_STAFF_PASSWORD: str

    DOMAIN_NAME: str = "localhost"
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()