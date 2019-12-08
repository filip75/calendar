from rest_framework.test import APIRequestFactory

from users.models import Relation, User
from users.permissions import IsCoachPermission


class TestIsCoachPermission:
    def test_permission(self, coach: User, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        request.user = coach

        permission = IsCoachPermission()

        assert permission.has_permission(request, None)

    def test_permission_negative(self, runner: User, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        request.user = runner

        permission = IsCoachPermission()

        assert not permission.has_permission(request, None)

    def test_has_object_permission(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        request.user = relation.coach

        permission = IsCoachPermission()

        assert permission.has_object_permission(request, None, relation)

    def test_has_object_permission_negative(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        new_coach = User.objects.create(username='new_coach', email='new_coach@users.com', is_coach=True)
        request.user = new_coach

        permission = IsCoachPermission()

        assert not permission.has_object_permission(request, None, relation)
