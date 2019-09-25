# class UsernameExists(forms.CharField):
#
#     def validate(self, value):
#         super().validate(value)
#         if not User.objects.filter(username=value).exists():
#             raise ValidationError('Username doesn\'t exist', code='invalid')
#
#
# class RunnerInviteForm(forms.Form):
#     runner = UsernameExists(max_length=150)
#
#
# class CancelInviteForm(forms.Form):
#     runner = UsernameExists(max_length=150, widget=forms.HiddenInput())
