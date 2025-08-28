from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from aylim_system.views import backup_db_view, restore_db_view

urlpatterns = [
    path('mumiyo/', admin.site.urls),
    path('admin/backup-db/', backup_db_view, name='backup_db'),
    path('admin/restore-db/', restore_db_view, name='restore_db'),
    path('', include(('users.urls', 'users'), namespace='users')), # 'users' namespace'ini qo'shing
    path('tests/', include('tests.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)