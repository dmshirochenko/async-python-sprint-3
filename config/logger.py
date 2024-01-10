from config.config import settings

LOG_FORMAT = "%(asctime)s - %(name)s -  - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s"
LOG_DEFAULT_HANDLERS = ["console", "file"]  # Added "file" here

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": LOG_FORMAT},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {  # New File Handler
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": "app.log",  # Specify your log file name here
            "mode": "w",  # Append mode
        },
    },
    "loggers": {
        "": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": settings.app_debug_level,
        },
    },
    "root": {
        "level": "INFO",
        "formatter": "verbose",
        "handlers": LOG_DEFAULT_HANDLERS,
    },
}
