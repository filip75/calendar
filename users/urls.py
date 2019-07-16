from django.urls import path

from users.views import SignUpViewView

urlpatterns = [
    path('signup/', SignUpViewView.as_view(), name='users-signup'),
]
