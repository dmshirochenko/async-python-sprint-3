import os

from pydantic import Field
from pydantic_settings import BaseSettings


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_file = ".env"
ENV_FILE_PATH = os.path.join(BASE_DIR, env_file)


class Settings(BaseSettings):
    # Общие настройки
    app_debug_level: str = Field("INFO", env="APP_DEBUG_LEVEL")
    base_dir: str = Field(BASE_DIR)

    class Config:
        env_file = ENV_FILE_PATH


settings = Settings()
