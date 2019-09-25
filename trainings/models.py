from users.models import User

# class RunnerCoachRelation(models.Model):
#     runner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_runner')
#     coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_coach', blank=True)
#     connection_date = models.DateField(default=date.today)
#     is_accepted = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f'runner:{str(self.runner)}-coach:{str(self.coach)}'
