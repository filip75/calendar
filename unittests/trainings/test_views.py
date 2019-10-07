import datetime
from typing import List
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.response import TemplateResponse
from django.test import RequestFactory
from django.urls import reverse
from freezegun import freeze_time

from trainings.models import Training
from trainings.views import TrainingCreateView, TrainingDetailView, TrainingListView
from users.models import Relation, RelationStatus, User

DATE = datetime.date(year=2019, month=9, day=30)
SOME_MONDAY = DATE - datetime.timedelta(days=DATE.weekday())
DAY = datetime.timedelta(days=1)


class TestCreateTrainingView:
    def test_has_training(self, setup_db: List[Relation], request_factory: RequestFactory):
        t1 = Training.objects.create(relation=setup_db[0], date=DATE, description='description')
        t2 = Training.objects.create(relation=setup_db[1], date=DATE, description='description')
        request = request_factory.post(reverse('trainings-create'),
                                       data={'runners': [relation.runner.username for relation in setup_db],
                                             'date': '2019-09-30',
                                             'description': 'new_description',
                                             'force': 'False',
                                             'visible_since': ''})
        request.user = setup_db[0].coach
        view = TrainingCreateView.as_view()

        with patch('trainings.views.messages'):
            response: TemplateResponse = view(request)

        assert all(relation in response.context_data['has_training'] for relation in [t1, t2])

    def test_has_training_override(self, setup_db: List[Relation], request_factory: RequestFactory):
        Training.objects.create(relation=setup_db[0], date=DATE, description='description')
        Training.objects.create(relation=setup_db[1], date=DATE, description='description')
        runners = [setup_db[0].runner, setup_db[1].runner]
        request = request_factory.post(reverse('trainings-create'),
                                       data={'runners': [runner.username for runner in runners],
                                             'date': '30.09.2019',
                                             'description': 'new_description',
                                             'force': 'True',
                                             'visible_since': ''})
        request.user = setup_db[0].coach
        view = TrainingCreateView.as_view()

        with patch('trainings.views.messages'):
            view(request)

        assert Training.objects.filter(relation__runner=runners[0], relation__coach=setup_db[0].coach,
                                       date=DATE).get().description == 'new_description'
        assert Training.objects.filter(relation__runner=runners[1], relation__coach=setup_db[1].coach,
                                       date=DATE).get().description == 'new_description'

    def test_force_true(self, setup_db: List[Relation], request_factory: RequestFactory):
        Training.objects.create(relation=setup_db[0], date=DATE, description='description')
        request = request_factory.post(reverse('trainings-create'),
                                       data={'runners': [setup_db[0].runner.username],
                                             'date': '2019-09-30',
                                             'description': 'new_description',
                                             'force': 'False',
                                             'visible_since': ''})
        request.user = setup_db[0].coach
        view = TrainingCreateView.as_view()

        with patch('trainings.views.messages'):
            response: TemplateResponse = view(request)

        assert response.context_data['form'].data['force'] is True

    def test_login_required(self, coach: User, request_factory: RequestFactory):
        request = request_factory.get(reverse('trainings-create'))
        request.user = coach
        view = TrainingCreateView.as_view()

        response: TemplateResponse = view(request)

        assert response.status_code == 200

    def test_login_required_negative(self, request_factory: RequestFactory):
        request = request_factory.get(reverse('trainings-create'))
        request.user = AnonymousUser()
        view = TrainingCreateView.as_view()

        response: TemplateResponse = view(request)

        assert response.status_code == 302

    def test_is_coach(self, coach: User, request_factory: RequestFactory):
        request = request_factory.get(reverse('trainings-create'))
        request.user = coach
        view = TrainingCreateView.as_view()

        response: TemplateResponse = view(request)

        assert response.status_code == 200

    def test_is_coach_negative(self, runner: User, request_factory: RequestFactory):
        request = request_factory.get(reverse('trainings-create'))
        request.user = runner
        view = TrainingCreateView.as_view()

        with pytest.raises(PermissionDenied):
            view(request)

    def test_get_runner(self, setup_db: List[Relation], request_factory: RequestFactory):
        request = request_factory.get(f"{reverse('trainings-create')}?runner={setup_db[0].runner.username}")
        request.user = setup_db[0].coach
        view = TrainingCreateView.as_view()

        with patch('trainings.views.messages'):
            response: TemplateResponse = view(request)

        assert response.context_data['form'].initial['runners'] == [setup_db[0].runner.username]

    def test_get_date(self, setup_db: List[Relation], request_factory: RequestFactory):
        request = request_factory.get(f"{reverse('trainings-create')}?date={SOME_MONDAY}")
        request.user = setup_db[0].coach
        view = TrainingCreateView.as_view()

        with patch('trainings.views.messages'):
            response: TemplateResponse = view(request)

        assert response.context_data['form'].initial['date'] == SOME_MONDAY


class TestTrainingListView:
    @freeze_time(SOME_MONDAY)
    def test_return_only_current_week(self, relation: Relation, request_factory: RequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        t0 = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY - DAY)
        t1 = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY)
        t2 = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY + DAY)
        t3 = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY + 2 * DAY)
        t4 = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY + 6 * DAY)
        t5 = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY + 7 * DAY)
        this_week = [t1, t2, t3, t4]
        others = [t0, t5]
        request = request_factory.get(reverse('trainings-list', kwargs={'runner': relation.runner.username}))
        request.user = relation.coach
        view = TrainingListView.as_view()

        response: TemplateResponse = view(request, runner=relation.runner.username)

        object_list = response.context_data['object_list']
        assert all(training in object_list for training in this_week) \
               and not any(training in object_list for training in others)

    def test_date_format(self, relation: Relation, request_factory: RequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        request = request_factory.get(
            f"{reverse('trainings-list', kwargs={'runner': relation.runner.username})}?date=2019-09-30")
        request.user = relation.coach
        view = TrainingListView.as_view()

        response: TemplateResponse = view(request, runner=relation.runner.username)

        assert response.status_code == 200

    def test_date_format_negative(self, relation: Relation, request_factory: RequestFactory):
        request = request_factory.get(
            f"{reverse('trainings-list', kwargs={'runner': relation.runner.username})}?date=30-09-2019")
        request.user = relation.coach
        view = TrainingListView.as_view()

        response: TemplateResponse = view(request, runner=relation.runner.username)

        assert response.status_code == 400

    def test_wrong_runner(self, relation: Relation, request_factory: RequestFactory):
        for status in RelationStatus:
            if status == RelationStatus.ESTABLISHED:
                continue
            relation.status = status
            relation.save()
            request = request_factory.get(reverse('trainings-list', kwargs={'runner': relation.runner.username}))
            request.user = relation.coach
            view = TrainingListView.as_view()

            response: TemplateResponse = view(request, runner=relation.runner.username)

            assert response.status_code == 400

    @freeze_time(SOME_MONDAY)
    def test_fill_week(self, relation: Relation, request_factory: RequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        monday = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY)
        wednesday = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY + 2 * DAY)
        thursday = Training.objects.create(relation=relation, description='description', date=SOME_MONDAY + 3 * DAY)
        request = request_factory.get(reverse('trainings-list', kwargs={'runner': relation.runner.username}))
        request.user = relation.coach
        view = TrainingListView.as_view()

        response: TemplateResponse = view(request, runner=relation.runner.username)

        queryset: List[Training] = response.context_data['object_list']
        assert len(queryset) == 7
        assert queryset[0] == monday and queryset[2] == wednesday and queryset[3] == thursday
        assert queryset[1].date == SOME_MONDAY + 1 * DAY and queryset[1].pk is None
        assert queryset[4].date == SOME_MONDAY + 4 * DAY and queryset[1].pk is None
        assert queryset[5].date == SOME_MONDAY + 5 * DAY and queryset[1].pk is None
        assert queryset[6].date == SOME_MONDAY + 6 * DAY and queryset[1].pk is None

    def test_login_required(self, coach: User, relation: Relation, request_factory: RequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        request = request_factory.get(reverse('trainings-list', kwargs={'runner': relation.runner.username}))
        request.user = coach
        view = TrainingListView.as_view()

        response: TemplateResponse = view(request, runner=relation.runner.username)

        assert response.status_code == 200

    def test_login_required_negative(self, request_factory: RequestFactory):
        request = request_factory.get(reverse('trainings-list', kwargs={'runner': 'some_runner'}))
        request.user = AnonymousUser()
        view = TrainingListView.as_view()

        response: TemplateResponse = view(request)

        assert response.status_code == 302

    def test_is_coach_negative(self, runner: User, request_factory: RequestFactory):
        request = request_factory.get(reverse('trainings-list', kwargs={'runner': 'some_runner'}))
        request.user = runner
        view = TrainingListView.as_view()

        with pytest.raises(PermissionDenied):
            view(request)


class TestTrainingDetailView:
    def test_exists(self, relation: Relation, request_factory: RequestFactory):
        Training.objects.create(relation=relation, date=SOME_MONDAY, description='description')
        view = TrainingDetailView.as_view()
        request = request_factory.get(
            reverse('trainings-entry', kwargs={'runner': relation.runner.username, 'date': SOME_MONDAY}))
        request.user = relation.coach

        response = view(request, runner=relation.runner.username, date=SOME_MONDAY.strftime('%Y-%m-%d'))

        assert response.status_code == 200

    def test_not_exist(self, relation: Relation, request_factory: RequestFactory):
        view = TrainingDetailView.as_view()
        request = request_factory.get(
            reverse('trainings-entry', kwargs={'runner': relation.runner.username, 'date': SOME_MONDAY}))
        request.user = relation.coach

        with pytest.raises(Http404):
            view(request, runner=relation.runner.username, date=SOME_MONDAY.strftime('%Y-%m-%d'))

    def test_edit_url(self, relation: Relation, request_factory: RequestFactory):
        training = Training.objects.create(relation=relation, date=SOME_MONDAY, description='description')
        view = TrainingDetailView.as_view()
        request = request_factory.get(
            reverse('trainings-entry', kwargs={'runner': relation.runner.username, 'date': SOME_MONDAY}))
        request.user = relation.coach

        with patch('trainings.views.TrainingDetailView.get_object') as get_object:
            get_object.side_effect = lambda: training
            response = view(request, runner=relation.runner.username, date=SOME_MONDAY.strftime('%Y-%m-%d'))
            response = response.render()

        assert reverse('trainings-entry', kwargs={'runner': relation.runner.username, 'date': SOME_MONDAY}) in str(
            response.content)
