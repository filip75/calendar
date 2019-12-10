from django.utils.translation import gettext
from rest_framework import serializers

from trainings.models import Training
from users.models import Relation, RelationStatus


class TrainingSerializer(serializers.HyperlinkedModelSerializer):
    relation = serializers.HyperlinkedRelatedField(view_name='users-api-runner-profile', lookup_field='pk',
                                                   queryset=Relation.objects.all())
    url = serializers.HyperlinkedIdentityField(view_name='trainings-api-entry', lookup_url_kwarg='pk')

    class Meta:
        model = Training
        fields = ['url', 'relation', 'date', 'description', 'execution', 'visible_since']
        read_only_fields = ['execution']

    def validate_relation(self, value: Relation):
        if value.coach != self.context['request'].user or value.status != RelationStatus.ESTABLISHED:
            raise serializers.ValidationError(gettext("Invalid data"))
        return value
