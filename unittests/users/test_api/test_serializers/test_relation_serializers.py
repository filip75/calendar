import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from users.models import Relation, RelationStatus, User
from users.serializers.relation_serializer import RelationSerializer


class TestRelationSerializer:
    def test_serialize(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        serializer = RelationSerializer(instance=relation, context={'request': request})

        assert serializer.data['runner_name'] == relation.runner.username
        assert serializer.data['details'] == 'http://testserver' + reverse('users-api-runner-profile',
                                                                           kwargs={'pk': relation.id})
        assert serializer.data['status'] == relation.status
        assert serializer.data['trainings'] == 'http://testserver' + reverse('users-api-runner-trainings',
                                                                             kwargs={'pk': relation.id})
        assert serializer.data['nickname'] == relation.nickname

    def test_create(self, coach: User, runner: User, api_factory: APIRequestFactory):
        request = api_factory.post('/', data={'runner': runner.username})
        request.user = coach

        serializer = RelationSerializer(data={'runner': runner.username}, context={'request': request})
        serializer.is_valid()
        instance: Relation = serializer.save()

        assert instance.runner == runner
        assert instance.coach == coach
        assert instance.status == RelationStatus.INVITED_BY_COACH

    def test_update(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.patch('/', data={'nickname': 'new_nickname'})
        request.user = relation.coach

        serializer = RelationSerializer(instance=relation, data={'nickname': 'new_nickname'},
                                        context={'request': request}, partial=True)
        serializer.is_valid()
        instance: Relation = serializer.save()

        assert instance.nickname == 'new_nickname'

    def test_deserialize_negative(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.post('/', data={'runner': relation.runner.username})
        request.user = relation.coach

        serializer = RelationSerializer(data={'runner': relation.runner.username}, context={'request': request})
        assert serializer.is_valid() is False

        serializer = RelationSerializer(data={'runner': relation.runner.username}, context={'request': request})
        relation.status = RelationStatus.ESTABLISHED
        assert serializer.is_valid() is False

        serializer = RelationSerializer(data={'runner': '1'}, context={'request': request})
        assert serializer.is_valid() is False

    def test_validate_runner(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        request.user = relation.coach
        serializer = RelationSerializer(instance=relation, context={'request': request})

        with pytest.raises(ValidationError):
            serializer.validate_runner(relation.runner.username)

    def test_validate_runner_negative(self, runner: User, coach: User, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        request.user = coach
        serializer = RelationSerializer(instance=None, context={'request': request})

        serializer.validate_runner(runner.username)

    def test_validate_nickname(self, relation: Relation, api_factory: APIRequestFactory):
        runner = User.objects.create(username='new_runner', email='new_runner@users.com', is_runner=True)
        Relation.objects.create(runner=runner, coach=relation.coach, nickname='new_nickname')
        request = api_factory.get('/')
        request.user = relation.coach
        serializer = RelationSerializer(instance=relation, context={'request': request})

        with pytest.raises(ValidationError):
            serializer.validate_nickname('new_nickname')

    def test_validate_nickname_negative(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        request.user = relation.coach
        serializer = RelationSerializer(instance=relation, context={'request': request})

        serializer.validate_nickname('new_nickname')
