from passlib.hash import bcrypt
from passlib.utils import bcrypt64

from user_management.core.config.settings import get_settings

pwd_context = bcrypt.using(
    salt=bcrypt64.repair_unused(get_settings().encrypt_salt.get_secret_value())
)
