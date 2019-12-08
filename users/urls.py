from django.contrib.auth.views import LoginView
from django.urls import path

import users.api_views.coach_views as api_coach_views
import users.views as views

urlpatterns = [
    path('logout/', views.logout_view, name='users-logout'),
    path('signup/', views.SignUpView.as_view(), name='users-signup'),
    path('login/', LoginView.as_view(template_name='users/login.html', redirect_authenticated_user=True),
         name='users-login'),
    path('profile/', views.RunnerProfileView.as_view(), name='users-profile'),
    path('runners/', views.RunnerListView.as_view(), name='users-runners'),
    path('runners/<slug:runner>/', views.RunnerDetailView.as_view(), name='users-runners-detail'),
    path('runners/<slug:runner>/delete', views.RunnerDeleteView.as_view(), name='users-runners-delete'),
    path('invites/', views.InviteListView.as_view(), name='users-invites'),
    path('invites/<str:coach>/', views.AcceptInviteView.as_view(), name='users-invites-accept'),

    path('api/runners/', api_coach_views.RunnerListView.as_view(), name='users-api-runners'),
    path('api/runners/<slug:pk>', api_coach_views.RunnerDetailView.as_view(), name='users-api-runner-profile'),
    path('api/runners/<slug:pk>/trainings', api_coach_views.RunnerListView.as_view(), name='users-api-runner-trainings')
]
