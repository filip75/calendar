from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.db import models


class UserType(Enum):
    RUNNER = 0
    COACH = 1


class User(AbstractUser):
    # email = models.EmailField('email address', blank=True, unique=True)
    is_runner = models.BooleanField(default=False)
    is_coach = models.BooleanField(default=False)
    trainer = models.ForeignKey('User', on_delete=models.CASCADE, null=True)
    # coaches = models.ManyToManyField('User')


class RelationRequest(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE)
    runner = models.ForeignKey(User, on_delete=models.CASCADE)
