import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from unittests.conftest import PASSWORD, RUNNER_USERNAME
from users.models import UserType


class TestAuth:
    @pytest.mark.usefixtures('transactional_db')
    def test_register(self):
        client = APIClient()

        response = client.post(reverse('rest_register'),
                               data={'username': RUNNER_USERNAME,
                                     'password1': PASSWORD,
                                     'password2': PASSWORD,
                                     'email': f'{RUNNER_USERNAME}@users.com',
                                     'user_type': UserType.RUNNER.value})

        assert 'key' in response.data

    @pytest.mark.usefixtures('transactional_db')
    def test_register_negative(self):
        client = APIClient()

        response = client.post(reverse('rest_register'),
                               data={'username': RUNNER_USERNAME,
                                     'password1': PASSWORD,
                                     'password2': '',
                                     'email': f'{RUNNER_USERNAME}@users.com',
                                     'user_type': UserType.RUNNER.value})

        assert 'key' not in response.data

    @pytest.mark.usefixtures('runner')
    def test_login(self):
        client = APIClient()

        response = client.post(reverse('rest_login'), data={'username': RUNNER_USERNAME, 'password': PASSWORD})

        assert 'key' in response.data

    @pytest.mark.usefixtures('runner')
    def test_login_negative(self):
        client = APIClient()

        response = client.post(reverse('rest_login'), data={'username': 'anhdshafhsa', 'password': PASSWORD})

        assert 'key' not in response.data
