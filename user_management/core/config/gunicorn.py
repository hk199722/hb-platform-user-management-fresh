from user_management.core.config.settings import get_settings

settings = get_settings()

workers = 2
threads = 1
timeout = 120
worker_class = "user_management.core.config.workers.FactoryUvicornWorker"
accesslog = "-"  # Log to stdout.
