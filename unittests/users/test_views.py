from typing import Type
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest
from django.template.response import TemplateResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views.generic import DeleteView

from users.models import Relation, RelationStatus, User, UserType
from users.views import AcceptInviteView, DoesntHaveTrainerMixin, InviteListView, RunnerDeleteView, RunnerDetailView, \
    RunnerListView, SignUpView, UserIsCoachMixin, UserIsRunnerMixin


class TestRunnerListView:
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
        for i in range(16):
            runner = User.objects.create(username=f'runner{i}', is_runner=True, email=f'user{i}@users.com')
            Relation.objects.create(coach=coach, runner=runner)
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = coach

        response: TemplateResponse = RunnerListView.as_view()(request)

        assert len(response.context_data['object_list']) == 15

    def test_exclude_runner_invites(self, coach: User, runner: User, request_factory: RequestFactory):
        Relation.objects.create(runner=runner, coach=coach, status=RelationStatus.INVITED_BY_RUNNER)
        request: HttpRequest = request_factory.get(reverse('users-runners'))
        request.user = coach
        view = RunnerListView()
        view.request = request

        queryset = view.get_queryset()

        assert len(queryset) == 0

    def test_invite(self, coach: User, runner: User, request_factory: RequestFactory):
        request: HttpRequest = request_factory.post(reverse('users-runners'), data={'runner': runner.username})
        request.user = coach
        view = RunnerListView.as_view()

        with patch('users.views.messages') as messages:
            response: TemplateResponse = view(request)

        assert response.status_code == 200
        assert Relation.objects.filter(runner=runner, coach=coach).exists()
        assert messages.succces.callled()

    def test_invite_non_existing(self, coach: User, request_factory: RequestFactory):
        request: HttpRequest = request_factory.post(reverse('users-runners'), data={'runner': 'runner'})
        request.user = coach
        view = RunnerListView.as_view()

        with patch('users.views.messages') as messages:
            response: TemplateResponse = view(request)

        assert response.status_code == 200
        assert not Relation.objects.filter(runner__username='runner', coach=coach).exists()
        assert messages.warning.callled()

    def test_invite_has_trainer(self, coach: User, runner: User, request_factory: RequestFactory):
        c = User.objects.create(username='another_coach', email='another_coach@users.com', is_coach=True)
        Relation.objects.create(runner=runner, coach=c, status=RelationStatus.ESTABLISHED)
        request: HttpRequest = request_factory.post(reverse('users-runners'), data={'runner': 'runner'})
        request.user = coach
        view = RunnerListView.as_view()

        with patch('users.views.messages') as messages:
            response: TemplateResponse = view(request)

        assert response.status_code == 200
        assert not Relation.objects.filter(runner=runner, coach=coach).exists()
        assert messages.warning.callled()

    def test_invite_already_invited(self, coach: User, runner: User, request_factory: RequestFactory):
        Relation.objects.create(runner=runner, coach=coach, status=RelationStatus.INVITED_BY_COACH)
        request: HttpRequest = request_factory.post(reverse('users-runners'), data={'runner': runner.username})
        request.user = coach
        view = RunnerListView.as_view()

        with patch('users.views.messages') as messages:
            response: TemplateResponse = view(request)

        assert response.status_code == 200
        assert messages.warning.callled()


class TestRunnerDetailView:

    def test_only_established(self, coach: User, request_factory: RequestFactory):
        runners = []
        for idx, status in enumerate(RelationStatus):
            runner = User.objects.create(username=f'runner{idx}', is_runner=True, email=f'runner{idx}@users.com')
            relation = Relation.objects.create(coach=coach, runner=runner, status=status)
            runners.append((runner, relation))
        view = RunnerDetailView.as_view()

        for runner, relation in runners:
            request: HttpRequest = request_factory.get(
                reverse('users-runners-detail', kwargs={'runner': runner.username}))
            request.user = coach

            if relation.status == RelationStatus.ESTABLISHED:
                response: TemplateResponse = view(request, runner=runner.username)
                assert response.status_code == 200
                assert response.context_data['object'] == relation
            else:
                with pytest.raises(Http404):
                    view(request, runner=runner.username)

    def test_shows_only_runners_of_user(self, coach: User, relation: Relation, request_factory: RequestFactory):
        runner = User.objects.create(username='another_runner', email='another_runner@users.com', is_runner=True)
        Relation.objects.create(runner=runner, coach=coach, status=RelationStatus.INVITED_BY_RUNNER)
        request: HttpRequest = request_factory.get(reverse('users-runners-detail', kwargs={'runner': runner.username}))
        request.user = coach
        view = RunnerDetailView()
        view.setup(request, runner=runner.username)

        with pytest.raises(Http404):
            view.dispatch(request)

    def test_change_nickname(self, coach: User, runner: User, relation: Relation, request_factory: RequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        request: HttpRequest = request_factory.post(reverse('users-runners-detail', kwargs={'runner': runner.username}),
                                                    data={'nickname': 'new_nickname'})
        request.user = coach
        view = RunnerDetailView.as_view()

        with patch('users.views.messages') as messages:
            view(request, runner=runner.username)

        relation.refresh_from_db()
        assert relation.nickname == 'new_nickname'
        assert messages.succces.callled()

    def test_change_nickname_already_exists(self, coach: User, runner: User, relation: Relation,
                                            request_factory: RequestFactory):
        another_runner = User.objects.create(username='another_runner', email='another_runner@users.com',
                                             is_runner=True)
        Relation.objects.create(runner=another_runner, coach=coach, status=RelationStatus.ESTABLISHED,
                                nickname='new_nickname')
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        request: HttpRequest = request_factory.post(reverse('users-runners-detail', kwargs={'runner': runner.username}),
                                                    data={'nickname': 'new_nickname'})
        request.user = coach
        view = RunnerDetailView.as_view()

        with patch('users.views.messages') as messages:
            view(request, runner=runner.username)

        relation.refresh_from_db()
        assert relation.nickname is None
        assert messages.warning.callled()


class TestRunnerDeleteView:
    def test_show_all_but_invited_by_runner(self, coach: User, request_factory: RequestFactory):
        runners = []
        for idx, status in enumerate(RelationStatus):
            runner = User.objects.create(username=f'runner{idx}', is_runner=True, email=f'runner{idx}@users.com')
            relation = Relation.objects.create(coach=coach, runner=runner, status=status)
            runners.append((runner, relation))
        view = RunnerDeleteView.as_view()

        for runner, relation in runners:
            request: HttpRequest = request_factory.get(
                reverse('users-runners-delete', kwargs={'runner': runner.username}))
            request.user = coach
            view.request = request

            if relation.status == RelationStatus.INVITED_BY_RUNNER:
                with pytest.raises(Http404):
                    view(request, runner=runner.username)
            else:
                assert view(request, runner=runner.username).status_code == 200

    def test_post(self, relation: Relation, request_factory: RequestFactory):
        request: HttpRequest = request_factory.post(
            reverse('users-runners-delete', kwargs={'runner': relation.runner.username}))
        request.user = relation.coach
        RunnerDeleteView.post = DeleteView.post
        view = RunnerDeleteView.as_view()

        view(request, runner=relation.runner.username)

        assert not Relation.objects.filter(id=relation.id).exists()


class TestAcceptInviteView:
    @pytest.fixture(autouse=True)
    def set_relation_to_invited(self, relation: Relation):
        relation.status = RelationStatus.INVITED_BY_COACH
        relation.save()

    def test_get_object(self, relation: Relation, request_factory: RequestFactory):
        request = request_factory.get(reverse('trainings-invites-accept', kwargs={'coach': relation.coach.username}))
        request.user = relation.runner
        view = AcceptInviteView()
        view.setup(request, coach=relation.coach.username)

        obj = view.get_object()

        assert obj == relation

    def test_post(self, relation: Relation, request_factory: RequestFactory):
        request = request_factory.post(reverse('trainings-invites-accept', kwargs={'coach': relation.coach.username}))
        request.user = relation.runner
        view = AcceptInviteView.as_view()
        get_object_mock = Mock()
        AcceptInviteView.get_object = get_object_mock

        with patch('users.views.messages'):
            view(request, coach=relation.coach.username)

        get_object_mock().save.assert_called()


class TestInviteListView:
    @pytest.mark.usefixtures('transactional_db')
    def test_get_queryset(self, request_factory: RequestFactory):
        runner1 = User.objects.create(username='runner1', email='runner1@users.com', is_runner=True)
        runner2 = User.objects.create(username='runner2', email='runner2@users.com', is_runner=True)
        coach1 = User.objects.create(username='coach1', email='coach1@users.com', is_coach=True)
        coach2 = User.objects.create(username='coach2', email='coach2@users.com', is_coach=True)
        coach3 = User.objects.create(username='coach3', email='coach3@users.com', is_coach=True)
        r1 = Relation.objects.create(runner=runner1, coach=coach1, status=RelationStatus.INVITED_BY_COACH)
        Relation.objects.create(runner=runner1, coach=coach2, status=RelationStatus.INVITED_BY_RUNNER)
        r2 = Relation.objects.create(runner=runner1, coach=coach3, status=RelationStatus.INVITED_BY_COACH)
        Relation.objects.create(runner=runner2, coach=coach1, status=RelationStatus.INVITED_BY_COACH)
        Relation.objects.create(runner=runner2, coach=coach2, status=RelationStatus.INVITED_BY_RUNNER)
        Relation.objects.create(runner=runner2, coach=coach3, status=RelationStatus.INVITED_BY_COACH)
        request = request_factory.get(reverse('trainings-invites'))
        request.user = runner1
        view = InviteListView()
        view.setup(request)

        queryset = view.get_queryset()

        assert len(queryset) == 2 and r1 in queryset and r2 in queryset


class TestPermissionMixins:
    @staticmethod
    def dummy_view() -> (Mock, Type):
        dispatch_mock = Mock()

        class DummyView:
            dispatch = dispatch_mock

        return dispatch_mock, DummyView

    def test_doesnt_have_trainer(self, relation: Relation, request_factory: RequestFactory):
        relation.status = RelationStatus.INVITED_BY_COACH
        relation.save()
        dispatch_mock, dummy_view = self.dummy_view()

        class T(DoesntHaveTrainerMixin, dummy_view):
            pass

        t = T()
        request: HttpRequest = request_factory.get('/')
        request.user = relation.runner
        t.request = request

        t.dispatch(request)

        dispatch_mock.assert_called()

        relation.status = RelationStatus.ESTABLISHED
        relation.save()

        with pytest.raises(PermissionDenied):
            t.dispatch(request)

    @pytest.mark.parametrize('mixin, user', [[UserIsCoachMixin, 'coach'], [UserIsRunnerMixin, 'runner']])
    def test_is(self, request_factory: RequestFactory, user: str, mixin: Type, request):
        user = request.getfixturevalue(user)
        dispatch_mock, dummy_view = self.dummy_view()

        class T(mixin, dummy_view):
            pass

        t = T()
        request: HttpRequest = request_factory.get('/')
        request.user = user
        t.request = request

        t.dispatch(request)

        dispatch_mock.assert_called()

    @pytest.mark.parametrize('mixin, user', [[UserIsCoachMixin, 'runner'], [UserIsRunnerMixin, 'coach']])
    def test_is_negative(self, request_factory: RequestFactory, user: str, mixin: Type, request):
        user = request.getfixturevalue(user)
        dispatch_mock, dummy_view = self.dummy_view()

        class T(mixin, dummy_view):
            pass

        t = T()
        request: HttpRequest = request_factory.get('/')
        request.user = user
        t.request = request

        with pytest.raises(PermissionDenied):
            t.dispatch(request)

        dispatch_mock.assert_not_called()


class TestSignupView:
    @pytest.mark.usefixtures('transactional_db')
    def test_has_token(self, request_factory: RequestFactory):
        request = request_factory.post(reverse('users-signup'),
                                       data={'username': 'runner1',
                                             'email': 'runner1@users.com',
                                             'password1': 'testing321',
                                             'password2': 'testing321',
                                             'user_type': UserType.RUNNER.value
                                             })
        request.user = AnonymousUser()
        view = SignUpView.as_view()

        with patch('users.views.messages'):
            view(request)

        runner = User.objects.get(username='runner1')
        assert hasattr(runner, 'auth_token')
