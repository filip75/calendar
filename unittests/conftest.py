from typing import List

import pytest
from django.test import Client, RequestFactory

from users.models import Relation, RelationStatus, User


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def runner(transactional_db) -> User:
    user = User(username='runner', email='runner@users.com')
    user.is_runner = True
    user.save()
    return user


@pytest.fixture
def coach(transactional_db) -> User:
    user = User(username='coach', email='coach@users.com')
    user.is_coach = True
    user.save()
    return user


@pytest.fixture
def relation(runner: User, coach: User):
    relation = Relation(runner=runner, coach=coach)
    relation.save()
    return relation


@pytest.fixture()
def setup_db(transactional_db) -> List[Relation]:
    coach = User.objects.create(username='coach', email='coach@users.com', is_coach=True)
    runner1 = User.objects.create(username='runner1', email='runner1@users.com', is_runner=True)
    runner2 = User.objects.create(username='runner2', email='runner2@users.com', is_runner=True)
    relation1 = Relation.objects.create(coach=coach, runner=runner1, status=RelationStatus.ESTABLISHED)
    relation2 = Relation.objects.create(coach=coach, runner=runner2, status=RelationStatus.ESTABLISHED)

    return [relation1, relation2]
