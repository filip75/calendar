from typing import List

from trainings.forms import AddTrainingForm
from users.models import Relation, RelationStatus, User


class TestAddTrainingForm:
    def test_contains_only_established_runners(self, setup_db: List[Relation]):
        coach = setup_db[0].coach
        runners = [setup_db[0].runner, setup_db[1].runner]
        for idx, status in enumerate(RelationStatus):
            if status != RelationStatus.ESTABLISHED:
                r = User.objects.create(username=f'new_runner{idx}', email=f'new_runner{idx}@users.com', is_runner=True)
                Relation.objects.create(coach=coach, runner=r, status=status)

        form = AddTrainingForm(coach)

        choices = sorted([runner[0] for runner in form.fields['runners'].choices])
        runners = sorted([runner.username for runner in runners])
        assert runners == choices

    def test_not_required_fields(self, setup_db: List[Relation]):
        form = AddTrainingForm(setup_db[0].coach, data={'visible_since': '', 'force': 'False'})
        form.full_clean()

        assert 'force' not in form._errors
        assert 'visible_since' not in form._errors
