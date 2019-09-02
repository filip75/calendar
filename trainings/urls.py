from django.urls import path

from trainings.views import home

urlpatterns = [
    path('', home, name='trainings-home'),
]
