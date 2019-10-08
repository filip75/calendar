from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest
from django.template.response import TemplateResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views.generic import DeleteView

from users.models import Relation, RelationStatus, User
from users.views import RunnerDeleteView, RunnerDetailView, RunnerListView


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
            RunnerListView.as_view()(request)

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
    def test_login_required(self, coach: User, request_factory: RequestFactory, relation: Relation):
        request: HttpRequest = request_factory.get(
            reverse('users-runners-detail', kwargs={'runner': relation.runner.username}))
        request.user = coach
        relation.status = RelationStatus.ESTABLISHED
        relation.save()

        response = RunnerDetailView.as_view()(request, runner=relation.runner.username)

        assert response.status_code == 200

    def test_login_required_negative(self, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners-detail', kwargs={'runner': 'a'}))
        request.user = AnonymousUser()

        response = RunnerDetailView.as_view()(request, runner='a')

        assert response.status_code == 302

    def test_allow_only_coach(self, coach: User, request_factory: RequestFactory, relation: Relation):
        request: HttpRequest = request_factory.get(reverse('users-runners-detail',
                                                           kwargs={'runner': relation.runner.username}))
        request.user = coach
        relation.status = RelationStatus.ESTABLISHED
        relation.save()

        response = RunnerDetailView.as_view()(request, runner=relation.runner.username)

        assert response.status_code == 200

    def test_allow_only_coach_negative(self, runner: User, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners-detail', kwargs={'runner': 'a'}))
        request.user = runner

        with pytest.raises(PermissionDenied):
            RunnerDetailView.as_view()(request, runner='a')

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
    def test_login_required(self, coach: User, request_factory: RequestFactory, relation: Relation):
        request: HttpRequest = request_factory.get(
            reverse('users-runners-delete', kwargs={'runner': relation.runner.username}))
        request.user = coach

        response = RunnerDeleteView.as_view()(request, runner=relation.runner.username)

        assert response.status_code == 200

    def test_login_required_negative(self, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners-delete', kwargs={'runner': 'a'}))
        request.user = AnonymousUser()

        response = RunnerDeleteView.as_view()(request, runner='a')

        assert response.status_code == 302

    def test_allow_only_coach(self, coach: User, request_factory: RequestFactory, relation: Relation):
        request: HttpRequest = request_factory.get(reverse('users-runners-delete',
                                                           kwargs={'runner': relation.runner.username}))
        request.user = coach

        response = RunnerDeleteView.as_view()(request, runner=relation.runner.username)

        assert response.status_code == 200

    def test_allow_only_coach_negative(self, runner: User, request_factory: RequestFactory):
        request: HttpRequest = request_factory.get(reverse('users-runners-delete', kwargs={'runner': 'a'}))
        request.user = runner

        with pytest.raises(PermissionDenied):
            RunnerDeleteView.as_view()(request, runner='a')

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

# class TestSignupView:
#     def test_get(self, client: Client, user_register_form):
#         response = client.get('/signup/')
#
#         assert 200 == response.status_code
#         assert '<form' in str(response.content)
#
#     def test_post(self, user_register_form, request_factory: RequestFactory):
#         request: HttpRequest = request_factory.post(reverse('users-signup'), {})
#
#         # is_valid.is_valid = Mock(side_effect=lambda: True)
#         v = SignUpView.as_view(form_class=user_register_form)
#
#         response = v(request)
#         # response = client.post('/signup/', data={})
#
#         # assert is_valid.is_valid.assert_called()
#         # assert user_register_form.is_valid
#         assert response.status_code == 201
