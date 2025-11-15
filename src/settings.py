from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ProductStorage"
    PROJECT_VERSION: str = "0.0.1"
    DEBUG: bool = True
    CORS_ALLOWED_ORIGINS: str = "*"

    @property
    def origins(self) -> list[str]:
        return self.CORS_ALLOWED_ORIGINS.split(",")

    model_config = SettingsConfigDict(
        env_file='.env',
        env_ignore_empty=True,
        extra='ignore'
    )


settings = Settings()
