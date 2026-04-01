from pydantic_settings import BaseSettings, SettingsConfigDict

import os

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')

class Settings(BaseSettings):
    DATABASE_URL: str
    EXCHANGE: str = "binance"
    API_KEY: str = ""
    API_SECRET: str = ""
    RISK_PER_TRADE: float = 0.02
    MAX_POSITIONS: int = 5
    PARTIAL_TP: bool = True
    PARTIAL_TP_PCT: float = 0.5
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    model_config = SettingsConfigDict(env_file=env_path)

settings = Settings()
