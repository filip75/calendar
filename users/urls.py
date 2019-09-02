from django.contrib.auth.views import LoginView
from django.urls import path

from users.views import RunnerProfileView, SignUpView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='users-signup'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='users-login'),
    path('profile/', RunnerProfileView.as_view(), name='users-profile')
]
