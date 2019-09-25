from django.contrib.auth.views import LoginView
from django.urls import path

import users.views as views

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='users-signup'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='users-login'),
    path('profile/', views.RunnerProfileView.as_view(), name='users-profile'),
    path('runners/', views.RunnerListView.as_view(), name='users-runners'),
    path('runners/<int:pk>/', views.RunnerDetailView.as_view(), name='users-runners-detail')
]
