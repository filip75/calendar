from django.urls import path

from trainings import views
from trainings.views import home

urlpatterns = [
    path('', home, name='trainings-home'),
    path('trainings/create/', views.TrainingCreateView.as_view(), name='trainings-create'),
    path('trainings/<slug:runner>/', views.TrainingListView.as_view(), name='trainings-list'),
    path('trainings/<slug:runner>/<str:date>/', views.TrainingCreateView.as_view(),
         name='trainings-entry')  # TODO date regex
]
