from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StudentProfile
from .forms import CustomUserAdminCreationForm 

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