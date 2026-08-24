from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Notification Microservice"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./notification_db.sqlite"

    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_ORDER_EVENTS_TOPIC: str = "order-events"
    KAFKA_CONSUMER_GROUP: str = "notification-group"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
