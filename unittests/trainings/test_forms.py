# import pytest
#
# from trainings.forms import RunnerInviteForm
# from users.models import User
#
#
# class TestRunnerInviteForm:
#     def test_valid(self, runner: User):
#         form = RunnerInviteForm(data={'runner': runner.username})
#
#         assert form.is_valid() is True
#
#     @pytest.mark.usefixtures('transactional_db')
#     def test_username_length(self):
#         form = RunnerInviteForm(data={'runner': 'd' * 151})
#
#         assert form.is_valid() is False
