import os

from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_file = ".env"
ENV_FILE_PATH = os.path.join(BASE_DIR, env_file)


class HTTPError(BaseModel):
    message: str
    status_code: int


class ErrorMessages(BaseModel):
    invalid_json_format: HTTPError = HTTPError(message="Invalid JSON format", status_code=400)
    missing_required_data: HTTPError = HTTPError(message="Missing required data", status_code=400)
    user_has_not_been_found: HTTPError = HTTPError(message="User has not been found", status_code=400)
    unauthorized: HTTPError = HTTPError(message="Unauthorized", status_code=401)
    forbidden: HTTPError = HTTPError(message="Forbidden", status_code=403)
    not_found: HTTPError = HTTPError(message="Not Found", status_code=404)
    method_not_allowed: HTTPError = HTTPError(message="Method Not Allowed", status_code=405)
    internal_server_error: HTTPError = HTTPError(message="Internal Server Error", status_code=500)
    request_timeout_error: HTTPError = HTTPError(message="Request processing timed out", status_code=408)
    message_limit_reached: HTTPError = HTTPError(message="Message limit reached", status_code=429)
    database_error: HTTPError = HTTPError(message="Database error occurred", status_code=500)


class Settings(BaseSettings):
    # Общие настройки
    app_debug_level: str = Field("INFO", env="APP_DEBUG_LEVEL")
    base_dir: str = Field(BASE_DIR)
    max_request_time: int = Field(5, env="MAX_REQUEST_TIME")
    max_messages_per_hour: int = Field(20, env="MAX_MESSAGE_PER_HOUR")
    error_messages: ErrorMessages = ErrorMessages()


settings = Settings()
