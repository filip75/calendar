import pytest

from users.forms import RunnerInviteForm, UserRegisterForm
from users.models import UserType


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
                  'password1': 'testing321',
                  'password2': 'testing321',
                  'user_type': str(UserType.RUNNER.value)})
        assert form.is_valid() is True

    @pytest.mark.usefixtures('transactional_db')
    def test_save(self):
        form = UserRegisterForm(
            data={'username': 'coach',
                  'email': 'coach@users.com',
                  'password1': 'testing321',
                  'password2': 'testing321',
                  'user_type': str(UserType.COACH.value)})

        instance = form.save()
        assert instance.is_coach is True


class TestRunnerInviteForm:
    def test_max_length(self):
        form1 = RunnerInviteForm(data={'runner': 'x' * 151})
        form2 = RunnerInviteForm(data={'runner': 'x' * 150})

        assert form1.is_valid() is False
        assert form2.is_valid() is True
