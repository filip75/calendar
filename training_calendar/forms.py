from django.contrib.auth.forms import SetPasswordForm
from django.forms import CharField, Form, HiddenInput


class MultipleForm(Form):
    action = CharField(max_length=100, widget=HiddenInput())


class MultipleSetPasswordForm(SetPasswordForm, MultipleForm):
    pass
