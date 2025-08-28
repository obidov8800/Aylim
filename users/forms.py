from django import forms
from .models import StudentProfile
from django.core.exceptions import ValidationError

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Parol", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = StudentProfile
        fields = ('full_name', 'date_of_birth', 'passport_number', 'phone_number', 'address', 'group', 'profile_picture', 'password')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control', 
                'required': True,
                'accept': 'image/*',
                # O'zbekcha matnlar
                'data-browse-text': 'Fayl tanlash',
                'data-placeholder-text': 'Hech qanday fayl tanlanmagan',
                'data-required-text': 'Iltimos, fayl tanlang.'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'password':
                field.widget.attrs['class'] = 'form-control'
        
        # Rasm maydonini majburiy qilish
        self.fields['profile_picture'].required = True
        # O'zbekcha label
        self.fields['profile_picture'].label = "Profil rasmi"

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if not profile_picture:
            raise ValidationError("Iltimos, profil rasmini yuklang.")
        return profile_picture

    def save(self, commit=True):
        user = super().save(commit=False)
        # ID va username yaratish logikasi
        last_student = StudentProfile.objects.filter(student_id__startswith='S').order_by('student_id').last()
        if last_student and last_student.student_id:
            new_id_num = int(last_student.student_id[1:]) + 1
        else:
            new_id_num = 1
        user.student_id = f"S{new_id_num:04d}"
        user.username = user.student_id # username ham student_id bo'lsin
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
        widgets = {
            'profile_picture': forms.FileInput(attrs={'required': True})  # required qo'shildi
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rasm maydonini majburiy qilish
        self.fields['profile_picture'].required = True

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if not profile_picture:
            raise ValidationError("Profil rasmi majburiy.")
        return profile_picture

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
            
        return user


# Tahrirlash formasi
class CustomUserAdminChangeForm(forms.ModelForm):
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


class BroadcastNotificationForm(forms.Form):
    message_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'class': 'vLargeTextField'}), 
        label="Xabar matni",
        help_text="Ushbu xabar tanlangan barcha foydalanuvchilarga yuboriladi."
    )