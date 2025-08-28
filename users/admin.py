# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect
from .models import StudentProfile
from .forms import (CustomUserAdminCreationForm, CustomUserAdminChangeForm, BroadcastNotificationForm)
from tests.models import Bildirishnoma

class StudentProfileAdmin(UserAdmin):
    # Foydalanuvchini TAHRIRLASH sahifasi uchun maydonlarni to'liq qayta yozamiz
    fieldsets = (
        # Birinchi bo'lim: Login ma'lumotlari
        (None, {'fields': ('username', 'password')}),
        
        # Ikkinchi bo'lim: Shaxsiy ma'lumotlar
        ('Shaxsiy ma\'lumotlar', {'fields': ('full_name', 'rol', 'date_of_birth', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture')}),
        
        # Uchinchi bo'lim: Tyutor sozlamalari (faqat Tyutorlar uchun)
        ('Tyutor sozlamalari', {'fields': ('assigned_groups',)}),
        
        # To'rtinchi bo'lim: Huquqlar
        ('Huquqlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        
        # Beshinchi bo'lim: Telegram va boshqa sozlamalar
        ('Qo\'shimcha ma\'lumotlar', {'fields': ('telegram_id', 'telegram_verification_code', 'password_reset_code')}),
        
        # Oltinchi bo'lim: Muhim sanalar
        ('Muhim sanalar', {'fields': ('last_login', 'date_joined')}),
    )

    # Foydalanuvchi YARATISH sahifasi
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Shaxsiy ma`lumotlar', {
            'fields': ('full_name', 'rol', 'date_of_birth', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture')
        }),
        ('Tyutor sozlamalari', {
            'fields': ('assigned_groups',)
        }),
        ('Huquqlar', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )
    
    # Ro'yxatda ko'rinadigan maydonlar
    list_display = ('username', 'full_name', 'rol', 'student_id', 'is_staff')
    
    # Filtrlar
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'rol')
    
    # Qidirish maydonlari
    search_fields = ('username', 'full_name', 'passport_number', 'student_id')
    
    # Tartiblash
    ordering = ('username',)
    
    # Ko'pdan-ko'p maydonlar uchun gorizontal filtr
    filter_horizontal = ('groups', 'user_permissions', 'assigned_groups')
    
    def get_fieldsets(self, request, obj=None):
        """Tyutor bo'lmagan foydalanuvchilar uchun assigned_groups maydonini olib tashlaymiz"""
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj and obj.rol != StudentProfile.Role.TYUTOR:
            # Tyutor bo'lmagan foydalanuvchilar uchun 'Tyutor sozlamalari' bo'limini olib tashlaymiz
            fieldsets = [fs for fs in fieldsets if fs[0] != 'Tyutor sozlamalari']
        
        return fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """Tyutor bo'lmagan foydalanuvchilar uchun assigned_groups maydonini formadan olib tashlaymiz"""
        form = super().get_form(request, obj, **kwargs)
        
        if obj and obj.rol != StudentProfile.Role.TYUTOR:
            if 'assigned_groups' in form.base_fields:
                del form.base_fields['assigned_groups']
        
        return form
    
    def has_add_permission(self, request):
        """Faqat superuser yoki staff bo'lganlar foydalanuvchi qo'sha oladi"""
        return request.user.is_superuser or request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        """Faqat superuser yoki staff bo'lganlar foydalanuvchini tahrirlay oladi"""
        return request.user.is_superuser or request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        """Faqat superuser yoki staff bo'lganlar foydalanuvchini o'chira oladi"""
        return request.user.is_superuser or request.user.is_staff
    
    def has_view_permission(self, request, obj=None):
        """Faqat superuser yoki staff bo'lganlar foydalanuvchilarni ko'ra oladi"""
        return request.user.is_superuser or request.user.is_staff
    
    def get_queryset(self, request):
        """Tyutorlar faqat o'zlariga ajratilgan guruhlarni ko'radi"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            # Superuser hamma narsani ko'radi
            return qs
        elif request.user.rol == StudentProfile.Role.TYUTOR:
            # Tyutorlar faqat o'zlariga ajratilgan guruhlardagi foydalanuvchilarni ko'radi
            assigned_groups = request.user.assigned_groups.all()
            return qs.filter(group__in=assigned_groups)
        else:
            # Boshqalar faqat o'z ma'lumotlarini ko'radi
            return qs.filter(id=request.user.id)

# Modelni admin paneliga ro'yxatdan o'tkazamiz
admin.site.register(StudentProfile, StudentProfileAdmin)

@admin.action(description="Tanlangan foydalanuvchilarga bildirishnoma yuborish")
def send_notification_action(modeladmin, request, queryset):
    if 'apply' in request.POST:
        form = BroadcastNotificationForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message_text']
            count = 0
            for user in queryset:
                Bildirishnoma.objects.create(user=user, matn=message)
                count += 1
            modeladmin.message_user(request, f"{count} ta foydalanuvchiga bildirishnoma muvaffaqiyatli yuborildi.")
            return redirect(request.get_full_path())
    else:
        form = BroadcastNotificationForm()

    return render(request, 'admin/send_notification_form.html', {
        'title': 'Bildirishnoma yuborish',
        'items': queryset,
        'form': form,
    })