from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from users.models import Relation
from users.permissions import IsCoachPermission
from users.serializers.relation_serializer import RelationSerializer


class RunnerListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsCoachPermission]
    queryset = Relation.objects.all()
    filter_backends = [OrderingFilter]
    ordering_fields = ['username']
    serializer_class = RelationSerializer

    def get_queryset(self):
        return super().get_queryset().filter(coach=self.request.user)


class RunnerDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Relation.objects.all()
    lookup_url_kwarg = 'pk'
    serializer_class = RelationSerializer
    permission_classes = [IsAuthenticated, IsCoachPermission]
