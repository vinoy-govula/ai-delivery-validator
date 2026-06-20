import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    runtime_manager_base_url: str = "http://localhost:8001"
    gateway_base_url: str = "http://localhost:8000"
    gateway_api_key: str = ""
    control_centre_base_url: str = "http://localhost:8002"
    docker_compose_command: str = "docker compose"


settings = Settings(
    runtime_manager_base_url=os.getenv("RUNTIME_MANAGER_BASE_URL", "http://localhost:8001"),
    gateway_base_url=os.getenv("AI_PLATFORM_BASE_URL", "http://localhost:8000"),
    gateway_api_key=os.getenv("AI_PLATFORM_API_KEY", ""),
)
