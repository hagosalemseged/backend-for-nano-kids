from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #-------------------------------------------------
    # Database
    #-------------------------------------------------
    DATABASE_URL: str

    #-------------------------------------------------
    # JWT / Auth
    #-------------------------------------------------
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # -------------------------------------------------
    # Cloudflare R2
    # -------------------------------------------------
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET_NAME: str | None = None
    R2_ENDPOINT_URL: str | None = None
    R2_PUBLIC_URL: str | None = None
    R2_ACCOUNT_ID: str | None = None
    R2_REGION: str = "auto"

     # -------------------------------------------------
    # SMTP / Email
    # -------------------------------------------------

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()