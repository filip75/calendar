import datetime
from unittest.mock import Mock

import pytest
from django.http import Http404
from django.urls import reverse
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from training_calendar.utils import format_date
from trainings.api_views.trainings_coach import TrainingsCoachViewSet
from trainings.models import Training
from unittests.trainings.test_views import SOME_MONDAY
from users.models import Relation, User


class TestTrainingsCoachViewSet:
    def test_get_object(self, relation: Relation, api_factory: APIRequestFactory):
        training = Training.objects.create(relation=relation, date=SOME_MONDAY, description='description')
        request = api_factory.get(f'{reverse("trainings-api-entry", kwargs={"pk": training.pk})}')
        request.user = relation.coach
        view = TrainingsCoachViewSet()
        view.setup(request, pk=training.pk)

        result = view.get_object()

        assert result == training

    def test_get_object_not_found(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get(f'{reverse("trainings-api-entry", kwargs={"pk": 123})}')
        request.user = relation.coach
        view = TrainingsCoachViewSet()
        view.setup(request, pk=123)

        with pytest.raises(Http404):
            view.get_object()

    def test_get_object_permission_denied(self, relation: Relation, api_factory: APIRequestFactory):
        training = Training.objects.create(relation=relation, date=SOME_MONDAY, description='description')
        request = api_factory.get(f'{reverse("trainings-api-entry", kwargs={"pk": training.pk})}')
        coach2 = User.objects.create(username='coach2', email='coach2@users.com', is_coach=True)
        request.user = coach2
        view = TrainingsCoachViewSet()
        view.setup(Request(request), pk=training.pk)

        with pytest.raises(PermissionDenied):
            view.get_object()

    def test_get_query_set(self, relation: Relation, api_factory: APIRequestFactory):
        training = Training.objects.create(relation=relation, date=SOME_MONDAY, description='description')
        request = api_factory.get(f'{reverse("trainings-api-list", kwargs={"relation": relation.pk})}')
        force_authenticate(request, relation.coach)
        view = TrainingsCoachViewSet()
        view.setup(Request(request), relation=relation.pk)

        result = view.get_queryset()

        assert training in result

    def test_get_query_set_dates(self, relation: Relation, api_factory: APIRequestFactory):
        Training.objects.create(relation=relation, date=format_date(datetime.datetime(2019, 12, 1)),
                                description='description')
        training = Training.objects.create(relation=relation, date=format_date(datetime.datetime(2019, 12, 2)),
                                           description='description')
        Training.objects.create(relation=relation, date=format_date(datetime.datetime(2019, 12, 4)),
                                description='description')
        request = api_factory.get(f'{reverse("trainings-api-list", kwargs={"relation": relation.pk})}'
                                  f'?start_date=2019-12-2&end_date=2019-12-3')
        request.user = relation.coach
        view = TrainingsCoachViewSet()
        view.setup(request, relation=relation.pk)

        result = view.get_queryset()

        assert training in result
        assert 1 == len(result)

        view = TrainingsCoachViewSet.as_view({'get': 'list'})
        force_authenticate(request, relation.coach)

        response = view(request, relation=relation.pk)

        assert response.status_code == 200

    def test_get_query_set_dates_negative(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get(f'{reverse("trainings-api-list", kwargs={"relation": relation.pk})}'
                                  f'?start_date=02-12-2019')
        request.user = relation.coach
        view = TrainingsCoachViewSet()
        view.setup(request, relation=relation.pk)

        with pytest.raises(ParseError):
            view.get_queryset()

        request = api_factory.get(f'{reverse("trainings-api-list", kwargs={"relation": relation.pk})}'
                                  f'?end_date=02-12-2019')
        request.user = relation.coach
        view.setup(request, relation=relation.pk)

        with pytest.raises(ParseError):
            view.get_queryset()

    def test_get_query_set_permission_denied(self, relation: Relation, api_factory: APIRequestFactory):
        coach = User.objects.create(username='coach2', email='coach2@users.com', is_coach=True)
        request = api_factory.get(f'{reverse("trainings-api-list", kwargs={"relation": relation.pk})}')
        request.user = coach

        view = TrainingsCoachViewSet()
        view.setup(request, relation=relation.pk)

        with pytest.raises(PermissionDenied):
            view.get_queryset()

    def test_create(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.post(f'{reverse("trainings-api-list", kwargs={"relation": relation.pk})}',
                                   data={'training': 'data'})
        force_authenticate(request, user=relation.coach)
        serializer_mock = Mock()
        serializer_mock().is_valid.return_value = True
        TrainingsCoachViewSet.serializer_class = serializer_mock
        view = TrainingsCoachViewSet.as_view({'post': 'create'})

        view(request)

        serializer_mock().save.assert_called()

    def test_update(self, relation: Relation, api_factory: APIRequestFactory):
        training = Training.objects.create(relation=relation, date='2019-12-12', description='description')
        request = api_factory.patch(f'{reverse("trainings-api-entry", kwargs={"pk": training.pk})}',
                                    data={'training': 'data'})
        force_authenticate(request, user=relation.coach)
        serializer_mock = Mock()
        serializer_mock().is_valid.return_value = True
        TrainingsCoachViewSet.serializer_class = serializer_mock
        view = TrainingsCoachViewSet.as_view({'patch': 'partial_update'})

        view(request, pk=training.pk)

        serializer_mock().save.assert_called()
