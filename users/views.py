from django.shortcuts import redirect
from django.views.generic import CreateView

from users.forms import UserRegisterForm
from users.models import User


class SignUpViewView(CreateView):
    model = User
    template_name = 'users/signup.html'
    form_class = UserRegisterForm

    def form_valid(self, form):
        form.save()
        return redirect('home')
