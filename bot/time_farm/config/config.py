from pydantic_settings import BaseSettings, SettingsConfigDict


class TimeFarmSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_ignore_empty=True)

    TF_CLAIM_RETRY: int = 3
    TF_SLEEP_BETWEEN_CLAIM: int = 180

    # SEND_CLAIM_AFTER: int = 0


settings = TimeFarmSettings()
