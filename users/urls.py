from django.urls import path
from . import views
from tests.views import notification_list_view

app_name = 'users'

urlpatterns = [
    # Asosiy sahifa - home
    path('', views.home_view, name='home'), 
    # Kirish sahifasi
    path('login/', views.login_view, name='login'), 
    # Ro'yxatdan o'tish sahifasi
    path('register/', views.register_view, name='register'),
    # Chiqish sahifasi
    path('logout/', views.logout_view, name='logout'),
    # Profil sahifasi
    path('profile/', views.profile_view, name='profile'),
    # Profilni yangilash sahifasi
    path('profile/update/', views.profile_update_view, name='profile_update'),
    # Bildirishnomalar sahifasi
    path('notifications/', notification_list_view, name='notification_list'),
]