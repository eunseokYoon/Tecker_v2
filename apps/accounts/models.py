from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    google_sub = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        db_table = "user"
