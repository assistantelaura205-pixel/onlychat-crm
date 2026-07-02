from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    SECRET_KEY: str = "dev-secret-change-me"
    TG_API_ID: int = 0
    TG_API_HASH: str = ""
    MEDIA_DIR: str = "./media_vault"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def sqlalchemy_url(self) -> str:
        url = self.DATABASE_URL.strip()
        if not url:
            return "sqlite:///./onlychat.db"
        # Railway fournit postgres:// — SQLAlchemy veut postgresql+pg8000:// ou postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
