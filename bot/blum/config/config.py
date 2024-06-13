from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: str = ""
    API_HASH: str = ""

    CLAIM_RETRY: int = 3
    SLEEP_BETWEEN_CLAIM: int = 180

    PLAY_GAME: bool = False


settings = Settings()
