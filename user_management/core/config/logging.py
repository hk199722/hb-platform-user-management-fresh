from user_management.core.config.settings import get_settings


LOGGING_LEVEL = "DEBUG" if get_settings().debug else "INFO"

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
            "level": LOGGING_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "user_management": {
            "handlers": ["console"],
            "propagate": False,
            "level": LOGGING_LEVEL,
        },
        "uvicorn": {
            "handlers": ["console"],
            "propagate": False,
            "level": LOGGING_LEVEL,
        },
        "gunicorn": {
            "handlers": ["console"],
            "propagate": False,
            "level": LOGGING_LEVEL,
        },
        "google.cloud.pubsub_v1": {
            "handlers": ["console"],
            "propagate": False,
            "level": LOGGING_LEVEL,
        },
        "sentry_sdk": {
            "handlers": ["console"],
            "propagate": False,
            "level": LOGGING_LEVEL,
        },
    },
}
