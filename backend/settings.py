from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    # GOOGLE CREDENTIALS
    CLIENT_ID: str
    CLIENT_SECRET: str
    
    # DATABASE
    DATABASE_URL: str
    DATABASE_NAME: str
    
    # AGENT SETTINGS
    MODEL_PROVIDER: str
    GROQ_API_KEY: str
    MODEL: str
    FIRST_RUN_DAYS: str
    SUBSEQUENT_RUN_HOURS: int
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

import os
if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here":
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
elif settings.GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY