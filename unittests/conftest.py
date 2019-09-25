import pytest
from django.test import Client, RequestFactory

from users.models import Relation, User


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
