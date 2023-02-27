import pydantic
from sqlalchemy.engine.url import URL


class Settings(pydantic.BaseSettings):
    SERVICE_NAME: str = "financial"
    ROOT_PATH: str = "/"

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    ALPHAVANTAGE_APIKEY: str = ""
    ALPHAVANTAGE_LAST_DAYS: int = 14
    ALPHAVANTAGE_SYMBOLS: tuple = ("IBM", "AAPL")

    # Ticker symbols for companies listed on the NYSE or AMEX are up to three letters long. Companies traded
    # on the Nasdaq National Market or Nasdaq Small-Cap exchanges commonly consist of four to five letters.
    MAX_SYMBOL_LENGTH: int = 5

    # PostgreSQL
    DB_DRIVER: str = "postgresql+asyncpg"
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "financial"
    DB_DATABASE: str = "financial"
    DB_PASSWORD: str = "financial"

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 0
    DB_ECHO: bool = False

    @property
    def DB_DSN(self) -> URL:
        return URL.create(self.DB_DRIVER, self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_DATABASE)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
