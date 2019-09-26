from typing import Tuple

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.edit import FormMixin

from training_calendar.forms import MultipleSetPasswordForm
from training_calendar.views import MultipleFormView
from users.forms import RunnerInviteForm, UserRegisterForm
from users.models import Relation, User


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
    template_name = 'users/runners.html'
    form_class = RunnerInviteForm
    paginate_by = 50

    def get_queryset(self):
        return Relation.objects.filter(coach=self.request.user).order_by('status')

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
            messages.error(self.request, gettext("User doesn't exist"))
            return
        runner: User = query.first()
        if runner.has_been_invited(self.request.user):
            messages.error(self.request, gettext('User has already been invited'))
            return
        if runner.has_coach():
            messages.error(self.request, gettext("User already has a coach"))
            return
        Relation.objects.create(coach=self.request.user, runner=runner)
        messages.success(self.request, gettext("User invited successfully"))


class RunnerDetailView(LoginRequiredMixin, UserIsCoachMixin, DetailView):
    template_name = 'users/runner_detail.html'
    model = Relation
    slug_field = "runner__username"
    slug_url_kwarg = "runner"

    def get_queryset(self):
        return Relation.objects.filter(coach=self.request.user)
