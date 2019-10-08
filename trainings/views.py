import datetime
from typing import Optional

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from trainings.forms import AddTrainingForm, UpdateTrainingForm
from trainings.models import Training
from users.models import Relation, RelationStatus
from users.views import UserIsCoachMixin

DAY = datetime.timedelta(days=1)
WEEK = datetime.timedelta(days=7)


def home(request):
    if not request.user.is_authenticated:
        return redirect('users-login')

    return render(request, 'trainings/home.html')


class TrainingCreateView(LoginRequiredMixin, UserIsCoachMixin, CreateView):
    template_name = 'trainings/training_create.html'
    model = Relation
    form_class = AddTrainingForm

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('date'):
            try:
                date = datetime.datetime.strptime(self.request.GET['date'], '%Y-%m-%d').date()
                initial['date'] = date
            except ValueError:
                pass
        if self.request.GET.get('runner'):
            initial['runners'] = [self.request.GET['runner']]
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['coach'] = self.request.user
        return kwargs

    def form_valid(self, form: AddTrainingForm):
        runners = form.cleaned_data['runners']
        force = form.cleaned_data['force']
        date = form.cleaned_data['date']
        has_training = Training.objects.filter(relation__runner__username__in=runners, date=date)
        if not force and has_training.exists():
            messages.warning(self.request, 'Some runners already have training for this day')
            form.data = form.data.copy()
            form.data['force'] = True
            return self.render_to_response(self.get_context_data(has_training=has_training, form=form))

        training = form.save(commit=False)
        # TODO 400 if not all relations exist
        for runner in runners:
            try:
                relation = Relation.objects.filter(coach=self.request.user, runner__username=runner).get()
            except Relation.DoesNotExist:
                return HttpResponseBadRequest()

            try:
                t = Training.objects.get(relation=relation, date=training.date)
                t.description = training.description
                t.save()
            except Training.DoesNotExist:
                training.pk = None
                training.relation = relation
                training.save()
        messages.success(self.request, "Successfully created training")
        return self.get(self.request)


class TrainingListView(LoginRequiredMixin, UserIsCoachMixin, ListView):
    template_name = 'trainings/training_list.html'
    model = Training
    monday = None
    previous_week = None
    next_week = None
    runner = None
    relation = None

    def get(self, request, *args, **kwargs):
        self.runner = self.kwargs['runner']
        relation = Relation.objects.filter(runner__username=self.runner, coach=self.request.user,
                                           status=RelationStatus.ESTABLISHED)
        if not relation.exists():
            return HttpResponseBadRequest()
        self.relation = relation.get()
        date = self.request.GET.get('date')
        if date:
            try:
                date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                return HttpResponseBadRequest()
        else:
            date = datetime.date.today()
        self.monday = date - datetime.timedelta(days=date.weekday())
        self.previous_week = self.monday - WEEK
        self.next_week = self.monday + WEEK
        self.object_list = self.get_queryset()
        return self.render_to_response(
            self.get_context_data(previous_week=self.previous_week, next_week=self.next_week,
                                  today=datetime.date.today(), relation=self.relation))

    def get_queryset(self):
        sunday = self.monday + datetime.timedelta(days=6)
        queryset = Training.objects.filter(relation__coach=self.request.user, relation__runner__username=self.runner,
                                           date__range=(self.monday, sunday))
        week_trainings = []
        idx = 0
        for i in range(7):
            if idx < len(queryset) and queryset[idx].date == self.monday + i * DAY:
                week_trainings.append(queryset[idx])
                idx += 1
            else:
                week_trainings.append(Training(relation=self.relation, date=self.monday + i * DAY))
        return week_trainings


class BaseEntryView:
    model = Training
    slug_field = 'relation__runner__username'
    slug_url_kwarg = 'runner'

    def set_date(self) -> Optional[HttpResponse]:
        date = self.kwargs.get('date')
        if date:
            try:
                self.date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                return HttpResponseBadRequest()
        else:
            return HttpResponseBadRequest()

    def get(self, request, *args, **kwargs):
        response = self.set_date()
        if response:
            return response
        return super().get(request, *args, *kwargs)

    def post(self, request, *args, **kwargs):
        response = self.set_date()
        if response:
            return response
        return super().post(request, *args, *kwargs)

    def get_queryset(self):
        return Training.objects.filter(relation__coach=self.request.user, date=self.date)


class TrainingDetailView(LoginRequiredMixin, UserIsCoachMixin, BaseEntryView, DetailView):
    template_name = 'trainings/training_detail.html'


class TrainingUpdateView(LoginRequiredMixin, UserIsCoachMixin, BaseEntryView, UpdateView):
    template_name = 'trainings/training_update.html'
    form_class = UpdateTrainingForm
