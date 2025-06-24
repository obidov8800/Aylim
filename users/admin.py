from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StudentProfile
from .forms import (CustomUserAdminCreationForm, CustomUserAdminChangeForm, BroadcastNotificationForm)
from tests.models import Bildirishnoma
# UserAdmin ni kengaytiramiz, chunki StudentProfile AbstractUser dan meros olgan
class StudentProfileAdmin(UserAdmin):
    # Foydalanuvchini TAHRIRLASH sahifasi uchun maydonlarni to'liq qayta yozamiz
    fieldsets = (
        # Birinchi bo'lim: Login ma'lumotlari
        (None, {'fields': ('username', 'password')}), # Parolni o'zgartirish linki uchun
        
        # Ikkinchi bo'lim: Shaxsiy ma'lumotlar
        ('Shaxsiy ma\'lumotlar', {'fields': ('full_name', 'rol', 'date_of_birth', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture')}),
        
        # Uchinchi bo'lim: Huquqlar
        ('Huquqlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        
        # To'rtinchi bo'lim: Muhim sanalar
        ('Muhim sanalar', {'fields': ('last_login', 'date_joined')}),
    )

    # Foydalanuvchi YARATISH sahifasi avvalgidek qoladi
    # Bu qismni avvalgi ko'rsatmalarimdan olingan deb hisoblaymiz, agar xato bersa, uni ham to'g'rilaymiz
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Shaxsiy ma`lumotlar', {'fields': ('full_name', 'rol', 'date_of_birth', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture')}),
    )
    
    # Ro'yxatda ko'rinadigan maydonlar
    list_display = ('username', 'full_name', 'rol', 'is_staff')
    
    # Qolgan sozlamalar
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'rol')
    search_fields = ('username', 'full_name', 'passport_number')
    ordering = ('username',)

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
                # ### TUZATISH: Maydon nomi 'matn' ga o'zgartirildi ###
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