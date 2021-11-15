from user_management.core.config.settings import get_settings

logging_config = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {
            "format": "%(levelname)s: [%(name)s:%(funcName)s:%(lineno)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "user_management": {
            "handlers": ["console"],
            "propagate": False,
            "level": "DEBUG" if get_settings().debug is True else "INFO",
        },
        "uvicorn": {
            "handlers": ["console"],
            "propagate": False,
            "level": "DEBUG" if get_settings().debug is True else "INFO",
        },
        "gunicorn": {
            "handlers": ["console"],
            "propagate": False,
            "level": "DEBUG" if get_settings().debug is True else "INFO",
        },
    },
}
