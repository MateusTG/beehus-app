from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str
    MONGO_DB_NAME: str = "platform_db"
    TIMEZONE: str = "America/Sao_Paulo"
    
    # RabbitMQ
    RABBITMQ_URL: str
    
    # Redis
    REDIS_URL: str

    # Selenium slot control
    SELENIUM_MAX_SLOTS: int = 5
    SELENIUM_NODE_COUNT: int = 5
    SELENIUM_NODE_MAX_SESSIONS: int = 1
    
    # Selenium
    SELENIUM_REMOTE_URL: str = "http://selenium-hub:4444/wd/hub"  # Selenium Grid Hub
    VNC_URL_BASE: str = "http://localhost"

    # Security
    DATABASE_ENCRYPTION_KEY: str = "qQkYhPB2wmkqTLcJxmiiKjYHrnJpDVRtMne4cxd8SpM="

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
