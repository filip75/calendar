from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.db import models


class UserType(Enum):
    RUNNER = 0
    COACH = 1


class User(AbstractUser):
    is_runner = models.BooleanField(default=False)
    is_coach = models.BooleanField(default=False)
