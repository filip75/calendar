import pytest

from users.forms import UserRegisterForm
from users.models import User, UserType


class TestForms:
    @pytest.mark.usefixtures('transactional_db')
    def test_runner_creation(self):
        form = UserRegisterForm(
            {'username': 'user1',
             'password1': 'Testing123',
             'password2': 'Testing123',
             'email': 'email@email.com',
             'user_type': UserType.RUNNER})

        user: User = form.save()

        assert 'user1' == user.username
