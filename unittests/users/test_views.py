from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.test import Client, RequestFactory
from django.urls import reverse

from users.models import Relation, User
from users.views import RunnerListView, SignUpView


@pytest.fixture
def user_register_form():
    class FormMock:
        def __init__(self, **_):
            pass

        def is_valid(self):
            return True

        def save(self, _=True):
            return Mock()

    return FormMock


class TestRunnersView:
    @pytest.mark.usefixtures('transactional_db')
    def test_getting_only_coaches_runners(self, request_factory: RequestFactory):
        runner1 = User(username='runner1', is_runner=True, email='runner1@users.com')
        runner1.save()
        runner2 = User(username='runner2', is_runner=True, email='runner2@users.com')
        runner2.save()
        runner3 = User(username='runner3', is_runner=True, email='runner3@users.com')
        runner3.save()
        coach1 = User(username='coach1', is_coach=True, email='coach1@users.com')
        coach1.save()
        coach2 = User(username='coach2', is_coach=True, email='coach2@users.com')
        coach2.save()
        relation1 = Relation(coach=coach1, runner=runner1)
        relation1.save()
        relation2 = Relation(coach=coach1, runner=runner2)
        relation2.save()
        relation3 = Relation(coach=coach1, runner=runner3)
        relation3.save()
        relation4 = Relation(coach=coach2, runner=runner1)
        relation4.save()
        relation5 = Relation(coach=coach2, runner=runner3)
        relation5.save()
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = coach2
        view = RunnerListView()
        view.request = request

        queryset = view.get_queryset()

        assert len(queryset) == 2 and relation4 in queryset and relation5 in queryset

    def test_paginate(self, coach: User, request_factory: RequestFactory):
        for i in range(51):
            runner = User.objects.create(username=f'runner{i}', is_runner=True, email=f'user{i}@users.com')
            Relation.objects.create(coach=coach, runner=runner)
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = coach

        response: TemplateResponse = RunnerListView.as_view()(request)

        assert len(response.context_data['object_list']) == 50

    def test_login_required(self, coach: User, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = coach

        response = RunnerListView.as_view()(request)

        assert response.status_code == 200

    def test_login_required_negative(self, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = AnonymousUser()

        response = RunnerListView.as_view()(request)

        assert response.status_code == 302

    def test_allow_only_coach(self, coach: User, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = coach

        response = RunnerListView.as_view()(request)

        assert response.status_code == 200

    def test_allow_only_coach_negative(self, runner: User, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = runner

        with pytest.raises(PermissionDenied):
            response = RunnerListView.as_view()(request)
            assert response.status_code == 403


class TestSignupView:
    def test_get(self, client: Client, user_register_form):
        response = client.get('/signup/')

        assert 200 == response.status_code
        assert '<form' in str(response.content)

    def test_post(self, user_register_form, request_factory: RequestFactory):
        request: HttpRequest = request_factory.post(reverse('users-signup'), {})

        # is_valid.is_valid = Mock(side_effect=lambda: True)
        v = SignUpView.as_view(form_class=user_register_form)

        response = v(request)
        # response = client.post('/signup/', data={})

        # assert is_valid.is_valid.assert_called()
        # assert user_register_form.is_valid
        assert response.status_code == 201
