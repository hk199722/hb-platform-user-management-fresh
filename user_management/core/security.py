from passlib.hash import bcrypt

from user_management.core.config.settings import get_settings

pwd_context = bcrypt.using(salt=get_settings().encrypt_salt.get_secret_value())
