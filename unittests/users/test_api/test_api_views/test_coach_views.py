from json import loads
from typing import List
from unittest.mock import Mock

import pytest
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from users.api_views.coach_views import RunnerDetailView, RunnerListView
from users.models import Relation, User
from users.permissions import IsCoachPermission


class TestRunnerListView:
    def test_permissions(self):
        view = RunnerListView()

        permissions = view.permission_classes

        assert IsCoachPermission in permissions and IsAuthenticated in permissions

    def test_get_queryset(self, setup_db: List[Relation], api_factory: APIRequestFactory):
        request = api_factory.get(reverse('users-api-runners'))
        request.user = setup_db[0].coach
        coach = User.objects.create(username='new_coach', email='new_coach@users.com', is_coach=True)
        runner = User.objects.create(username='new_runner', email='new_runner@users.com', is_runner=True)
        Relation.objects.create(runner=runner, coach=coach)
        view = RunnerListView()
        view.setup(request)

        queryset = view.get_queryset()

        assert len(queryset) == len(setup_db)
        for relation in setup_db:
            assert relation in queryset

    @pytest.mark.usefixtures('transactional_db')
    def test_default_pagination(self, api_factory: APIRequestFactory):
        coach = User.objects.create(username='coach', email='coach@users.com', is_coach=True)
        for i in range(60):
            runner = User.objects.create(username=f'runner_{i}', email=f'runner_{i}@users.com', is_runner=True)
            Relation.objects.create(runner=runner, coach=coach)
        request = api_factory.get(f"{reverse('users-api-runners')}?limit={20}&offset={20}")
        request._user = coach
        RunnerListView.permission_classes = []
        view = RunnerListView.as_view()

        result = view(request)

        json_response = loads(result.rendered_content)
        assert json_response['count'] == 60
        assert json_response['previous'] == f'http://testserver{reverse("users-api-runners")}?limit={20}'
        assert json_response['next'] == f'http://testserver{reverse("users-api-runners")}?limit={20}&offset={40}'
        assert 'results' in json_response

    def test_create(self, runner: User, coach: User, api_factory: APIRequestFactory):
        request = api_factory.post(reverse('users-api-runners'), data={'runner': runner.username})
        request.user = coach
        RunnerListView.permission_classes = []
        serializer_mock = Mock()
        RunnerListView.get_serializer_class = serializer_mock
        view = RunnerListView.as_view()

        view(request)

        serializer_mock()().save.assert_called()


class TestRunnerDetailView:
    def test_permissions(self):
        view = RunnerDetailView()

        permissions = view.permission_classes

        assert IsCoachPermission in permissions and IsAuthenticated in permissions

    def test_update(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.patch(reverse('users-api-runner-profile', kwargs={'pk': relation.runner_id}),
                                    data={'nickname': 'new_nickname'})
        request.user = relation.coach
        RunnerDetailView.permission_classes = []
        serializer_mock = Mock()
        RunnerDetailView.get_serializer_class = serializer_mock
        view = RunnerDetailView.as_view()

        view(request, pk=relation.runner_id)

        serializer_mock()().save.assert_called()
