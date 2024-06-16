from pydantic_settings import BaseSettings as BaseCoreSettings, SettingsConfigDict


class BaseSettings(BaseCoreSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: str = ""
    API_HASH: str = ""
