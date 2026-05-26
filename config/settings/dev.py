from .base import *

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "tecker",
        "USER": "tecker",
        "PASSWORD": "tecker",
        "HOST": "db",
        "PORT": "3306",
    }
}

# 개발환경: Android 에뮬레이터(10.0.2.2), iOS 시뮬레이터(localhost) 모두 허용
CORS_ALLOW_ALL_ORIGINS = True
ALLOWED_HOSTS = ["*"]
