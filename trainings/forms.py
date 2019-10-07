from django import forms
from django.forms import HiddenInput
from django.utils.translation import gettext

from trainings.models import Training
from users.models import Relation, RelationStatus, User


class AddTrainingForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'mw-250p'}))
    visible_since = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'mw-250p'}), required=False)
    force = forms.BooleanField(required=False, widget=HiddenInput())
    runners = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, label=gettext('Runners'))

    def __init__(self, coach: User, *args, **kwargs):
        super().__init__(*args, **kwargs)
        runners = [(relation.runner.username, relation.displayed_name) for relation in
                   Relation.objects.filter(coach=coach, status=RelationStatus.ESTABLISHED)]
        self.fields['runners'].choices = runners

    class Meta:
        model = Training
        fields = ['date', 'description', 'visible_since', 'runners', 'force']
