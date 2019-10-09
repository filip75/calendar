from django.urls import path

from trainings import views
from trainings.views import home

urlpatterns = [
    path('', home, name='trainings-home'),
    path('trainings/create/', views.TrainingCreateView.as_view(), name='trainings-create'),
    path('runners/<slug:runner>/trainings/', views.TrainingListView.as_view(), name='trainings-list'),
    path('runners/<slug:runner>/trainings/<str:date>/', views.TrainingListView.as_view(), name='trainings-list-entry'),
    path('runners/<slug:runner>/trainings/<str:date>/edit/', views.TrainingUpdateView.as_view(), name='trainings-edit'),
]

urlpatterns += [
    path('trainings/<str:date>/', views.TrainingListViewRunner.as_view(), name='trainings-entry-runner'),
    path('trainings/<str:date>/edit', views.TrainingUpdateViewRunner.as_view(), name='trainings-entry-edit-runner'),
    path('trainings/', views.TrainingListViewRunner.as_view(), name='trainings-runner')
]
