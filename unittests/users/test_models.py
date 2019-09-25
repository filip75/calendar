import pytest

from users.models import Relation, RelationStatus, User


class TestUser:
    def test_str(self):
        runner = User(username='user1', is_runner=True, email='1@1.com')

        assert str(runner) == 'username: user1, is_runner: True, is_coach: False'

    def test_default_values(self):
        runner = User(username='user1', email='1@1.com')

        assert runner.is_coach is False
        assert runner.is_runner is False

    @pytest.mark.usefixtures('transactional_db')
    def test_creation(self):
        runner = User(username='user1', is_runner=True, email='1@1.com')
        runner.save()

    def test_has_coach_positive(self, runner: User, relation: Relation):
        relation.status = RelationStatus.ESTABLISHED
        relation.save()

        assert runner.has_coach() is True

    @pytest.mark.usefixtures('relation')
    def test_has_coach_negative_invited(self, runner: User):
        assert runner.has_coach() is False

    def test_has_coach_negative_not_invited(self, runner: User):
        assert runner.has_coach() is False

    @pytest.mark.usefixtures('relation')
    def test_hes_been_invited(self, runner: User, coach: User):
        assert runner.has_been_invited(coach) is True

    def test_hes_been_invited_negative(self, runner: User, coach: User):
        assert runner.has_been_invited(coach) is False


class TestRelation:
    def test_str(self, runner: User, coach: User):
        r = Relation(runner=runner, coach=coach)
        r.save()

        assert str(r) == f'Relation of runner ({runner}) and coach ({coach})'

    def test_creation(self, runner: User, coach: User):
        r = Relation(runner=runner, coach=coach)
        r.save()

    def test_get_coaches(self, runner: User, coach: User):
        r = Relation(runner=runner, coach=coach)
        r.save()

        assert runner.coaches[0] == coach
        assert coach.runners.all()[0] == runner

    def test_default_status(self, runner: User, coach: User):
        r = Relation(runner=runner, coach=coach)

        assert r.status == RelationStatus.INVITED_BY_COACH

    def test_displayed_name(self, relation: Relation):
        assert relation.displayed_name == relation.runner.username
        relation.nickname = 'runner nickname'
        assert relation.displayed_name == 'runner nickname'
