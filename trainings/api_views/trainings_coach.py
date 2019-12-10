from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from training_calendar.utils import date_from_string
from trainings.models import Training
from trainings.serializers.training_serializer import TrainingSerializer
from users.models import Relation
from users.permissions import IsCoachPermission


class TrainingsCoachViewSet(ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsCoachPermission]

    def get_queryset(self):
        relation = self.kwargs.get('relation')
        try:
            if Relation.objects.get(pk=relation).coach != self.request.user:
                raise PermissionDenied()
        except (Relation.DoesNotExist, ValueError):
            raise NotFound()

        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            try:
                start_date = date_from_string(start_date)
            except ValueError:
                raise ParseError('date format should be yyyy-mm-dd')
        if end_date:
            try:
                end_date = date_from_string(end_date)
            except ValueError:
                raise ParseError('date format should be yyyy-mm-dd')

        objects = Training.objects.filter(relation=relation)
        if start_date:
            objects = objects.filter(date__gte=str(start_date))
        if end_date:
            objects = objects.filter(date__lte=end_date)
        return objects.all()

    def get_object(self):
        pk = self.kwargs.get('pk')
        obj = get_object_or_404(Training, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj
