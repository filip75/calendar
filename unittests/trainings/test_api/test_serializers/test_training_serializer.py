import datetime
from json import dumps

import pytest
from django.urls import reverse
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from trainings.models import Training
from trainings.serializers.training_serializer import TrainingSerializer
from users.models import Relation, RelationStatus


class TestTrainingSerializer:
    def test_serialize(self, relation: Relation, api_factory: APIRequestFactory):
        training = Training.objects.create(relation=relation, date='2019-12-12', description="description")
        relation.status = RelationStatus.ESTABLISHED
        request = api_factory.get('/')
        serializer = TrainingSerializer(training, context={'request': request})

        expected = \
            {'url': 'http://testserver' + reverse('trainings-api-entry', kwargs={'pk': training.pk}),
             'relation': 'http://testserver' + reverse('users-api-runner-profile', kwargs={'pk': training.relation.pk}),
             'date': '2019-12-12',
             'description': "description",
             'execution': None,
             'visible_since': None}

        assert dumps(serializer.data, sort_keys=True) == dumps(expected, sort_keys=True)

    def test_create(self, relation: Relation, api_factory: APIRequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        request = api_factory.get('/')
        request.user = relation.coach
        serializer = TrainingSerializer(
            data={'relation': reverse('users-api-runner-profile', kwargs={'pk': relation.pk}),
                  'date': '2019-12-12',
                  'description': 'description'},
            context={'request': request})

        serializer.is_valid()
        instance: Training = serializer.save()

        assert instance.relation == relation
        assert instance.date == datetime.date(2019, 12, 12)
        assert instance.description == 'description'
        assert instance.execution is None
        assert instance.visible_since is None

    def test_update(self, relation: Relation, api_factory: APIRequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        training = Training.objects.create(relation=relation, date='2019-12-12', description='description')
        request = api_factory.patch('/')
        request.user = relation.coach
        serializer = TrainingSerializer(instance=training,
                                        data={'url': reverse('trainings-api-entry', kwargs={'pk': training.pk}),
                                              'date': '2019-12-13',
                                              'description': 'new_description'},
                                        context={'request': request},
                                        partial=True)

        serializer.is_valid()
        instance: Training = serializer.save()

        assert instance.relation == relation
        assert instance.date == datetime.date(2019, 12, 13)
        assert instance.description == 'new_description'
        assert instance.execution is None
        assert instance.visible_since is None

    def test_validate_relation(self, relation: Relation, api_factory: APIRequestFactory):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        request = api_factory.get('/')
        request.user = relation.coach
        serializer = TrainingSerializer(data={}, context={'request': request})

        serializer.validate_relation(relation)

    def test_validate_relation_negative(self, relation: Relation, api_factory: APIRequestFactory):
        request = api_factory.get('/')
        request.user = relation.coach
        serializer = TrainingSerializer(data={}, context={'request': request})

        with pytest.raises(serializers.ValidationError):
            serializer.validate_relation(relation)

        relation.status = RelationStatus.ESTABLISHED
        relation.save()
        request.user = relation.runner
        serializer = TrainingSerializer(data={}, context={'request': request})

        with pytest.raises(serializers.ValidationError):
            serializer.validate_relation(relation)
