from django.contrib.auth.forms import UserCreationForm
from django.forms import CharField, ChoiceField, EmailField, RadioSelect

from training_calendar.forms import MultipleForm
from users.models import User, UserType

USER_TYPE_CHOICES = [(UserType.RUNNER, 'zawodnik'), (UserType.COACH, 'trener')]


class UserRegisterForm(UserCreationForm):
    email = EmailField()
    user_type = ChoiceField(choices=USER_TYPE_CHOICES, widget=RadioSelect, label='Typ użytkownika')

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


class UserInviteForm(MultipleForm):
    coach = CharField(max_length=100)

    def is_valid(self):
        return False
