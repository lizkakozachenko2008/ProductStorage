from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_VERSION: str
    DEBUG: bool
    CORS_ALLOWED_ORIGINS: str

    @property
    def origins(self) -> list[str]:
        return self.CORS_ALLOWED_ORIGINS.split(",")

    model_config = SettingsConfigDict(
        env_file='.env',
        env_ignore_empty=True,
        extra='ignore'
    )


settings = Settings()
