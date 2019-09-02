from unittest.mock import Mock

import pytest
from django.test import Client, RequestFactory
from django.urls import reverse

from users.views import SignUpView


@pytest.fixture
def user_register_form():
    class FormMock:
        def __init__(self, **_):
            pass

        def is_valid(self):
            return True

        def save(self, _=True):
            return Mock()

    return FormMock


class TestSignupView:
    def test_get(self, client: Client, user_register_form):
        response = client.get('/signup/')

        assert 200 == response.status_code
        assert '<form' in str(response.content)

    def test_post(self, user_register_form):
        factory = RequestFactory()
        request = factory.post(reverse('users-signup'), {})

        # is_valid.is_valid = Mock(side_effect=lambda: True)
        v = SignUpView.as_view(form_class=user_register_form)

        response = v(request)
        # response = client.post('/signup/', data={})

        # assert is_valid.is_valid.assert_called()
        # assert user_register_form.is_valid
        assert response.status_code == 201
