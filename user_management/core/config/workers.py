from uvicorn.workers import UvicornWorker


class FactoryUvicornWorker(UvicornWorker):
    """
    Custom/subclassed `UvicornWorker` class that lets us pass arguments to Uvicorn worker when
    instantiating it from `gunicorn` app server.
    """

    CONFIG_KWARGS = {
        "factory": True,
        "http": "auto",
        "loop": "auto",
    }
