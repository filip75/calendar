from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from users.models import Relation, RelationStatus, User


class RelationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api-runner-profile')
    trainings = serializers.HyperlinkedRelatedField(view_name='users-api-runner-trainings', read_only=True,
                                                    source='*')
    runner_name = serializers.CharField(source='runner.username', read_only=True)
    runner = serializers.CharField(max_length=150, write_only=True)

    class Meta:
        model = Relation
        fields = \
            ['runner_name', 'url', 'status', 'trainings', 'nickname', 'runner']
        read_only_fields = \
            ['runner_name', 'url', 'status', 'trainings']

    def validate_runner(self, value: str) -> str:
        try:
            runner = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(gettext("Runner doesn't exist"))
        if runner.has_coach():
            raise serializers.ValidationError(gettext("Runner already have a coach"))
        if Relation.objects.filter(runner=runner, coach=self.context['request'].user).exists():
            raise serializers.ValidationError(gettext("Runner has already been invited"))
        return value

    def validate_nickname(self, value: str) -> str:
        if Relation.objects.filter(nickname=value, coach=self.context['request'].user).exclude(
                id=self.instance.id).exists():
            raise serializers.ValidationError(gettext("Runner with this nickname already exists"))
        return value

    def create(self, validated_data: dict):
        runner = validated_data.get('runner')
        runner = get_object_or_404(User, username=runner, is_runner=True)
        return Relation.objects.create(runner=runner, coach=self.context['request'].user,
                                       status=RelationStatus.INVITED_BY_COACH)

    def update(self, instance: Relation, validated_data: dict):
        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.save()
        return instance
