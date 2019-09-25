from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView

from training_calendar.views import MultipleFormMixin


# from trainings.forms import RunnerInviteForm


def home(request):
    if not request.user.is_authenticated:
        return redirect('users-login')

    return render(request, 'trainings/home.html')


class InviteRunnerView(MultipleFormMixin, ListView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.add_form('invite', RunnerInviteForm, valid_func=self.invite_form_valid)

    def invite_form_valid(self, form: Form) -> HttpResponse:
        pass
