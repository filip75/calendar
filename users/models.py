from enum import IntEnum
from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy


def template_enum(cls):
    cls.do_not_call_in_templates = True
    return cls


class UserType(IntEnum):
    RUNNER = 0
    COACH = 1


@template_enum
class RelationStatus(IntEnum):
    ESTABLISHED = 0
    INVITED_BY_COACH = 1
    INVITED_BY_RUNNER = 2
    REVOKED = 3


class User(AbstractUser):
    email = models.EmailField(verbose_name='email address', blank=True, unique=True)
    is_runner = models.BooleanField(default=False)
    is_coach = models.BooleanField(default=False)
    runners = models.ManyToManyField('User', through='Relation')

    @property
    def coaches(self) -> List['User']:
        return [r.coach for r in self.runner_relation.all()]

    def has_coach(self) -> bool:
        return self.is_runner and self.runner_relation.filter(status=RelationStatus.ESTABLISHED).exists()

    def has_been_invited(self, user: 'User') -> bool:
        return self.runner_relation.filter(coach=user).exists()

    def __str__(self):
        return f'username: {self.username}, is_runner: {self.is_runner}, is_coach: {self.is_coach}'


class Relation(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coach_relation', blank=True)
    runner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='runner_relation')
    status = models.IntegerField(choices=[(s.value, s.name) for s in RelationStatus],
                                 default=RelationStatus.INVITED_BY_COACH, blank=True)
    nickname = models.CharField(max_length=150, null=True, blank=True, verbose_name=gettext_lazy('nickname'))

    class Meta:
        unique_together = [['runner', 'coach'], ['coach', 'nickname']]

    @property
    def displayed_name(self) -> str:
        return self.nickname if self.nickname else self.runner.username

    def __str__(self):
        return f'Relation of runner ({self.runner}) and coach ({self.coach})'

    def get_absolute_url(self):
        return reverse('users-runners-detail', kwargs={'runner': self.runner.username})
