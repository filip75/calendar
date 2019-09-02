from typing import Tuple

from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import CreateView

from training_calendar.forms import MultipleSetPasswordForm
from training_calendar.views import MultipleFormView
from users.forms import UserInviteForm, UserRegisterForm
from users.models import User


class RunnerProfileView(MultipleFormView):
    template_name = 'users/profile.html'

    def __init__(self, **kwargs):
        self.add_form('invite', UserInviteForm, self.invite_form_valid)
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


# @method_decorator(login_forbidden, name='dispatch') TODO login_forbidden
class SignUpView(CreateView):
    model = User
    template_name = 'users/signup.html'
    form_class = UserRegisterForm

    def form_valid(self, form):
        form.save()  # TODO super()?
        return redirect('trainings-home')


class InviteRunnerView:
    pass
