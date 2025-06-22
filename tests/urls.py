# tests/urls.py

from django.urls import path
from . import views

app_name = 'tests'

urlpatterns = [
    # Talabalar uchun manzillar
    path('', views.test_list_view, name='test_list'),
    path('take/<int:test_id>/', views.take_test_view, name='take_test'),
    path('result/<int:result_id>/', views.test_result_detail_view, name='test_result_detail'),
    
    # O'qituvchilar uchun manzillar
    path('my-tests/', views.teacher_test_list_view, name='teacher_test_list'),
    path('constructor/', views.test_constructor_view, name='create_test'),
    path('constructor/<int:test_id>/', views.test_constructor_view, name='edit_test'),
    path('delete-test/<int:test_id>/', views.delete_test_view, name='delete_test'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('attendance/student/', views.attendance_student_view, name='student_attendance'),
    path('attendance/management/', views.attendance_management_view, name='attendance_management'),
    path('ajax/get-attendance-data/', views.get_attendance_data_view, name='ajax_get_attendance_data'),
    path('ajax/update-attendance/', views.update_attendance_view, name='ajax_update_attendance'),
    # YETISHMAYOTGAN MANZIL QAYTA QO'SHILDI:
    path('<int:test_id>/import-questions/', views.import_questions_from_file_view, name='import_questions'),
]