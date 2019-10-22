from typing import Tuple

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError
from django.forms import Form
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext
from django.views.generic import CreateView, ListView
from django.views.generic.edit import DeleteView, FormMixin, UpdateView

from training_calendar.forms import MultipleSetPasswordForm
from training_calendar.views import MultipleFormView
from users.forms import RunnerInviteForm, UserRegisterForm
from users.models import Relation, RelationStatus, User


class UserIsCoachMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.is_coach


class UserIsRunnerMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.is_runner


class AnonymousUserMixin:
    redirect_url = None

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class RunnerProfileView(MultipleFormView):
    template_name = 'users/profile.html'

    def __init__(self, **kwargs):
        self.add_form('invite', RunnerInviteForm, self.invite_form_valid)
        self.add_form('change_password', MultipleSetPasswordForm, self.change_password_form_valid,
                      get_kwargs_func=self.change_password_form_get_kwargs)
        super().__init__(**kwargs)

    def invite_form_valid(self, form: Form) -> HttpResponse:
        return redirect('trainings-home')

    def change_password_form_valid(self, form: Form) -> HttpResponse:
        return redirect('trainings-home')

    def change_password_form_get_kwargs(self, form: str) -> Tuple[list, dict]:
        args, kwargs = self.get_form_kwargs(form)
        args.insert(0, self.request.user)
        return args, kwargs


def logout_view(request):
    logout(request)
    return redirect('trainings-home')


class SignUpView(AnonymousUserMixin, CreateView):
    model = User
    template_name = 'users/signup.html'
    form_class = UserRegisterForm
    redirect_url = reverse_lazy('trainings-home')

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('trainings-home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()  # TODO super()?
        messages.success(self.request, 'Account created')
        return redirect('users-login')


class RunnerListView(LoginRequiredMixin, UserIsCoachMixin, FormMixin, ListView):
    model = Relation
    template_name = 'users/coach_runners.html'
    form_class = RunnerInviteForm
    paginate_by = 15
    extra_context = {'RelationStatus': RelationStatus}

    def get_queryset(self):
        return Relation.objects.filter(coach=self.request.user).exclude(
            status=RelationStatus.INVITED_BY_RUNNER).order_by('status')

    def post(self, request):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        if form.is_valid():
            self.form_valid(form)
        return self.get(request)

    def form_valid(self, form):
        query = User.objects.filter(username=form.data['runner'], is_runner=True)
        if not query.exists():
            messages.warning(self.request, gettext("User doesn't exist"))
            return
        runner: User = query.first()
        if runner.has_been_invited(self.request.user):
            messages.warning(self.request, gettext('User has already been invited'))
            return
        if runner.has_coach():
            messages.warning(self.request, gettext("User already has a coach"))
            return
        Relation.objects.create(coach=self.request.user, runner=runner)
        messages.success(self.request, gettext("User invited successfully"))


class RunnerDetailView(LoginRequiredMixin, UserIsCoachMixin, UpdateView):
    template_name = 'users/coach_runner_detail.html'
    model = Relation
    slug_field = "runner__username"
    slug_url_kwarg = "runner"
    fields = ['nickname']
    extra_context = {'RelationStatus': RelationStatus}

    def get_queryset(self):
        return Relation.objects.filter(coach=self.request.user, status=RelationStatus.ESTABLISHED)

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "User's nickname set successfully")
            return response
        except IntegrityError:
            messages.warning(self.request, gettext("User with this nickname already exists"))
            return HttpResponseRedirect(self.get_success_url())


class RunnerDeleteView(LoginRequiredMixin, UserIsCoachMixin, DeleteView):
    template_name = 'users/coach_runner_delete.html'
    model = Relation
    slug_field = "runner__username"
    slug_url_kwarg = "runner"
    success_url = reverse_lazy('users-runners')
    extra_context = {'RelationStatus': RelationStatus}

    def get_queryset(self):
        return Relation.objects.filter(coach=self.request.user).exclude(status=RelationStatus.INVITED_BY_RUNNER)

    def post(self, request, *args, **kwargs):
        messages.info(request, gettext('Deleted successfully'))
        return super().post(request, *args, *kwargs)


class DoesntHaveTrainerMixin(UserPassesTestMixin):

    def test_func(self):
        return not self.request.user.has_coach()


class InviteListView(LoginRequiredMixin, DoesntHaveTrainerMixin, ListView):
    template_name = 'users/runner_invites_list.html'
    model = Relation

    def get_queryset(self):
        return Relation.objects.filter(runner=self.request.user, status=RelationStatus.INVITED_BY_COACH)


class AcceptInviteView(LoginRequiredMixin, DoesntHaveTrainerMixin, DeleteView):
    model = Relation
    template_name = 'users/runner_accept_invite.html'
    slug_field = 'coach__username'
    slug_url_kwarg = 'coach'
    success_url = reverse_lazy('trainings-runner')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.status = RelationStatus.ESTABLISHED
        success_url = self.get_success_url()
        self.object.save()
        return HttpResponseRedirect(success_url)

    def get_queryset(self):
        return Relation.objects.filter(runner=self.request.user, status=RelationStatus.INVITED_BY_COACH)

    def post(self, request, *args, **kwargs):
        messages.info(request, gettext('Accepted successfully'))
        return super().post(request, *args, *kwargs)
