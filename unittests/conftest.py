from typing import List

import pytest
from django.contrib.auth.hashers import make_password
from django.test import Client, RequestFactory
from rest_framework.test import APIRequestFactory

from users.models import Relation, RelationStatus, User

PASSWORD = 'testing321'
RUNNER_USERNAME = 'runner'
COACH_USERNAME = 'coach'


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def api_factory() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def runner(transactional_db) -> User:
    user = User(username=RUNNER_USERNAME, email='runner@users.com')
    user.is_runner = True
    user.password = make_password(PASSWORD)
    user.save()
    return user


@pytest.fixture
def coach(transactional_db) -> User:
    user = User(username=COACH_USERNAME, email='coach@users.com')
    user.is_coach = True
    user.password = make_password(PASSWORD)
    user.save()
    return user


@pytest.fixture
def relation(runner: User, coach: User):
    relation = Relation(runner=runner, coach=coach)
    relation.save()
    return relation


@pytest.fixture
def setup_db(transactional_db) -> List[Relation]:
    coach = User.objects.create(username='coach1', email='coach1@users.com', is_coach=True)
    runner1 = User.objects.create(username='runner1', email='runner1@users.com', is_runner=True)
    runner2 = User.objects.create(username='runner2', email='runner2@users.com', is_runner=True)
    relation1 = Relation.objects.create(coach=coach, runner=runner1, status=RelationStatus.ESTABLISHED)
    relation2 = Relation.objects.create(coach=coach, runner=runner2, status=RelationStatus.ESTABLISHED)

    return [relation1, relation2]
