from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import fields
from django.utils.translation import gettext

from users.models import User, UserType

USER_TYPE_CHOICES = [(UserType.RUNNER, gettext('runner')), (UserType.COACH, gettext('coach'))]


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect, label=gettext('User type'))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.data['user_type'] == UserType.RUNNER:
            user.is_runner = True
        elif self.data['user_type'] == UserType.COACH:
            user.is_coach = True
        if commit:
            user.save()
        return user


class RunnerInviteForm(forms.Form):
    runner = fields.CharField(max_length=150)
