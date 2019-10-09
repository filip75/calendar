from django.db import models
from django.urls import reverse

from users.models import Relation, User


class Training(models.Model):
    relation = models.ForeignKey(Relation, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    execution = models.TextField(null=True)
    visible_since = models.DateField(null=True, blank=True)

    class Meta:
        constraints = ['relation', 'date']

    def get_absolute_url(self):
        return reverse('trainings-list-entry', kwargs={'runner': self.relation.runner.username, 'date': self.date})

    def __str__(self) -> str:
        return f'Training(' \
            f'runner={self.relation.runner.username}, ' \
            f'trainer={self.relation.coach.username}, ' \
            f'date={self.date})'
