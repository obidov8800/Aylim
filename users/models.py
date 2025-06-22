# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Pasport raqamini tekshirish uchun validator
validate_passport_number = RegexValidator(
    regex=r'^[A-Z]{2}\d{7}$',
    message="Pasport raqami 2 ta lotin bosh harf va 7 ta raqamdan iborat bo'lishi kerak (Masalan: AA1234567)"
)

class StudentProfile(AbstractUser):
    class Role(models.TextChoices):
        TALABA = "TALABA", "Talaba"
        PEDAGOG = "PEDAGOG", "Pedagog"
        ADMIN = "ADMIN", "Admin"

    rol = models.CharField(max_length=50, choices=Role.choices, default=Role.TALABA, verbose_name="Roli")
    student_id = models.CharField(max_length=10, unique=True, null=True, blank=True, editable=False, verbose_name="Talabalik ID")
    
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism (F.I.Sh.)")
    date_of_birth = models.DateField(verbose_name="Tug'ilgan sana", null=True, blank=True)
    passport_number = models.CharField(max_length=9, unique=True, validators=[validate_passport_number], verbose_name='Pasport raqami')
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami")
    address = models.TextField(verbose_name="Yashash manzili", blank=True, null=True)
    group = models.ForeignKey('tests.Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Guruh")
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.png', blank=True, null=True, verbose_name='Profil rasmi')
    
    def __str__(self):
        return self.full_name or self.username

    def save(self, *args, **kwargs):
        # Agar bu yangi foydalanuvchi bo'lsa va uning student_id'si hali berilmagan bo'lsa
        if not self.student_id:
            prefix = ''
            if self.rol == self.Role.TALABA:
                prefix = 'S'
            elif self.rol == self.Role.PEDAGOG:
                prefix = 'T'
            elif self.rol == self.Role.ADMIN:
                # Adminlar uchun 'username'ni o'zi ishlatiladi, ID shart emas yoki A... formatda bo'lishi mumkin
                # Hozircha adminlar uchun alohida ID yaratmaymiz, ularni admin panel o'zi boshqaradi
                # Agar admin ham maxsus ID olishi kerak bo'lsa, shu yerga logikasini qo'shamiz
                pass
            
            if prefix:
                last_user = StudentProfile.objects.filter(student_id__startswith=prefix).order_by('student_id').last()
                if last_user and last_user.student_id:
                    new_id_num = int(last_user.student_id[1:]) + 1
                else:
                    new_id_num = 1
                
                new_student_id = f"{prefix}{new_id_num:04d}"
                self.student_id = new_student_id
                
                # Agar username bo'sh bo'lsa, unga ham shu ID'ni beramiz
                if not self.username:
                    self.username = new_student_id
        
        # Ota-klassning save() metodini chaqiramiz
        super().save(*args, **kwargs)