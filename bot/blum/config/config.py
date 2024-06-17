from pydantic_settings import BaseSettings, SettingsConfigDict


class BlumSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_ignore_empty=True)

    BLUM_CLAIM_RETRY: int = 3
    BLUM_SLEEP_BETWEEN_CLAIM: int = 180

    BLUM_PLAY_GAME: bool = False

    BLUM_SEND_CLAIM_AFTER: int = 0


settings = BlumSettings()
