from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import fields
from django.utils.translation import gettext

from users.models import User, UserType

USER_TYPE_CHOICES = [(UserType.RUNNER.value, gettext('runner')), (UserType.COACH.value, gettext('coach'))]


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    user_type = forms.TypedChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect, label=gettext('User type'),
                                       coerce=int)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']

    def save(self, commit=True) -> User:
        user = super().save(commit=False)
        user_type = int(self.data['user_type'])
        if user_type == UserType.RUNNER:
            user.is_runner = True
        elif user_type == UserType.COACH:
            user.is_coach = True
        if commit:
            user.save()
        return user


class RunnerInviteForm(forms.Form):
    runner = fields.CharField(max_length=150)
