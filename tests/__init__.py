import os

from dotenv import load_dotenv

import user_management

load_dotenv(f"{os.path.dirname(user_management.__path__[0])}/.env")
