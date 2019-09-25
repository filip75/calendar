import pytest

from users.forms import RunnerInviteForm, UserRegisterForm
from users.models import User, UserType


class TestUserRegisterForm:
    def test_init(self):
        UserRegisterForm()

    def test_empty_data(self):
        form = UserRegisterForm(data={})
        assert form.is_valid() is False

    @pytest.mark.usefixtures('transactional_db')
    def test_correct_data(self):
        form = UserRegisterForm(
            data={'username': 'runner',
                  'email': 'runner@users.com',
                  'password1': 'StrongPassword',
                  'password2': 'StrongPassword',
                  'user_type': UserType.RUNNER})
        assert form.is_valid() is True


class TestRunnerInviteForm:
    def test_correct_data(self, runner: User):
        form = RunnerInviteForm(data={'runner': runner.username})

        assert form.is_valid() is True

    @pytest.mark.usefixtures('transactional_db')
    def test_incorrect_data(self):
        form = RunnerInviteForm(data={'runner': 'freewge'})

        assert form.is_valid() is False
