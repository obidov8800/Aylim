# users/forms.py

from django import forms
from .models import StudentProfile # Faqat StudentProfile modelini import qilamiz!
from django.contrib.auth.forms import UserCreationForm
from tests.models import Group

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Parol", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = StudentProfile
        fields = ('full_name', 'date_of_birth', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture', 'password')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'password':
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        last_student = StudentProfile.objects.filter(student_id__startswith='S').order_by('student_id').last()
        if last_student and last_student.student_id:
            new_id_num = int(last_student.student_id[1:]) + 1
        else:
            new_id_num = 1
        
        new_student_id = f"S{new_id_num:04d}"
        user.student_id = new_student_id
        user.username = new_student_id
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
        return user


    
class CustomUserAdminCreationForm(forms.ModelForm):
    """
    Admin panelda foydalanuvchi yaratish uchun maxsus forma.
    """
    password = forms.CharField(label="Parol", widget=forms.PasswordInput)

    class Meta:
        model = StudentProfile
        fields = ('full_name', 'rol', 'date_of_birth', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture')

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # --- ID YARATISH LOGIKASI ---
        rol = self.cleaned_data.get('rol')
        prefix = ''
        if rol == StudentProfile.Role.TALABA:
            prefix = 'S'
        elif rol == StudentProfile.Role.PEDAGOG:
            prefix = 'T'
        elif rol == StudentProfile.Role.ADMIN:
            prefix = 'A'
        
        # Shu roldagi oxirgi foydalanuvchini topish
        last_user = StudentProfile.objects.filter(username__startswith=prefix).order_by('username').last()
        
        if last_user:
            # Agar mavjud bo'lsa, raqamini bittaga oshirish
            last_id_num = int(last_user.username[1:])
            new_id_num = last_id_num + 1
        else:
            # Agar bu roldagi birinchi foydalanuvchi bo'lsa
            new_id_num = 1
        
        # Yangi ID'ni formatlash (masalan, S0001)
        new_username = f"{prefix}{new_id_num:04d}"

        # username'ga yangi yaratilgan ID'ni berish
        user.username = new_username
        
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
            # Agar guruh tanlangan bo'lsa, profil yaratish (agar kerak bo'lsa)
            # Bizda group user modelining o'zida bo'lgani uchun alohida profil shart emas
            
        return user

# Tahrirlash formasi o'zgarishsiz qoladi
class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = '__all__'


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'phone_number', 'address', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'