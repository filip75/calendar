from django.contrib.auth.forms import SetPasswordForm
from django.forms import CharField, HiddenInput, forms


class MultipleFormMixin(forms.BaseForm):
    action = CharField(max_length=100, widget=HiddenInput())


class MultipleSetPasswordForm(MultipleFormMixin, SetPasswordForm):
    pass
