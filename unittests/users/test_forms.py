import pytest
from django.test import Client

from users.forms import UserRegisterForm
from users.models import User, UserType


class TestForms:
    @pytest.mark.usefixtures('transactional_db')
    def test_runner_creation(self):
        user_data = {'username': 'user1',
                     'password1': 'sdfjhusdfjhsiudfhjsf',
                     'password2': 'sdfjhusdfjhsiudfhjsf',
                     'email': 'email@email.com',
                     'user_type': UserType.RUNNER}
        form = UserRegisterForm(user_data)

        user: User = form.save()

        assert user.username == user_data['username']
        assert user.check_password(user_data['password1'])
        assert user.is_runner
        assert not user.is_coach
        assert user.runners.count() == 0

    def test_get(self, client: Client):
        response = client.get('/signup/')
        print(response.content)
