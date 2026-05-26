from .base import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "tecker_test",
        "USER": "tecker",
        "PASSWORD": "tecker",
        "HOST": "db",
        "PORT": "3306",
        "TEST": {"NAME": "tecker_test"},
    }
}

# 테스트 속도 향상
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
