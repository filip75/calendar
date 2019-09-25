# from datetime import date
#
# from trainings.models import RunnerCoachRelation
# from users.models import User
#
#
# class TestRunnerCoachRelation:
#     def test_str(self, runner: User, coach: User):
#         relation = RunnerCoachRelation(runner=runner, coach=coach)
#
#         assert str(relation) == f'runner:{str(relation.runner)}-coach:{str(relation.coach)}'
#
#     def test_default_date(self, runner: User, coach: User):
#         relation = RunnerCoachRelation(runner=runner, coach=coach)
#
#         assert relation.connection_date == date.today()
