from django.urls import path
from . import views
from tests.views import notification_list_view

app_name = 'users'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('notifications/', notification_list_view, name='notification_list'),
]