from configs import BaseSettings


class Settings(BaseSettings):
    BLUM_CLAIM_RETRY: int = 3
    BLUM_SLEEP_BETWEEN_CLAIM: int = 180

    BLUM_PLAY_GAME: bool = False

    BLUM_SEND_CLAIM_AFTER: int = 0


settings = Settings()
