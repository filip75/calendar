import random

from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand

from users.models import Relation, RelationStatus, User

PASSWORD = 'testing321'
EMAIL = '@users.com'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str)

    def handle(self, *args, **options):
        Relation.objects.all().delete()
        User.objects.all().delete()
        with open(f"{options['file_name']}") as file:
            for line in file:
                command, value = line.split()

                if command == 'runner':
                    User.objects.create(username=value, password=make_password(PASSWORD), email=f'{value}@users.com',
                                        is_runner=True)
                elif command == 'coach':
                    User.objects.create(username=value, password=make_password(PASSWORD), email=f'{value}@users.com',
                                        is_coach=True)
                elif command == 'relation':
                    runner, coach = value.split('-')
                    runner = User.objects.get(username=runner)
                    coach = User.objects.get(username=coach)
                    Relation.objects.create(runner=runner, coach=coach, status=random.choice(
                        [RelationStatus.ESTABLISHED, RelationStatus.INVITED_BY_COACH, RelationStatus.REVOKED]))
