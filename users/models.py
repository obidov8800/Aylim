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
        TYUTOR = "TYUTOR", "Tyutor"
        ADMIN = "ADMIN", "Admin"

    rol = models.CharField(max_length=50, choices=Role.choices, default=Role.TALABA, verbose_name="Roli")
    student_id = models.CharField(max_length=10, unique=True, null=True, blank=True, editable=False, verbose_name="ID raqami")
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name="Telegram ID")
    telegram_verification_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="Telegram uchun tasdiq kodi")
    password_reset_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="Parolni tiklash kodi")

    full_name = models.CharField(max_length=255, verbose_name="To'liq ism (F.I.Sh.)")
    date_of_birth = models.DateField(verbose_name="Tug'ilgan sana", null=True, blank=True)
    passport_number = models.CharField(max_length=9, unique=True, validators=[validate_passport_number], verbose_name='Pasport raqami')
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami")
    address = models.TextField(verbose_name="Yashash manzili", blank=True, null=True)
    group = models.ForeignKey('tests.Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Guruh")
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.png', blank=True, null=True, verbose_name='Profil rasmi')
    
    # Tyutorga ajratilgan guruhlar (ko'pdan-ko'p munosabat)
    assigned_groups = models.ManyToManyField(
        'tests.Group', 
        blank=True, 
        related_name='tyutors', 
        verbose_name="Ajratilgan guruhlar"
    )
    
    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ['-date_joined']

    def __str__(self):
        return self.full_name or self.username

def save(self, *args, **kwargs):
    # Agar bu yangi foydalanuvchi bo'lsa (pk yo'q) VA student_id hali belgilanmagan bo'lsa
    if not self.pk and not self.student_id:
        # ROLGA QARAB ID GENERATSIYA QILISH
        
        if self.rol == self.Role.TALABA:
            # Eng oxirgi TALABAni topamiz
            last_student = StudentProfile.objects.filter(rol=self.Role.TALABA).order_by('student_id').last()
            if last_student and last_student.student_id:
                try:
                    last_id_num = int(last_student.student_id[1:])
                    new_id_num = last_id_num + 1
                except (ValueError, IndexError):
                    new_id_num = 1
            else:
                new_id_num = 1
            self.student_id = f"S{new_id_num:04d}"

        elif self.rol == self.Role.PEDAGOG:
            # Eng oxirgi O'QITUVCHIni topamiz
            last_teacher = StudentProfile.objects.filter(rol=self.Role.PEDAGOG).order_by('student_id').last()
            if last_teacher and last_teacher.student_id:
                try:
                    last_id_num = int(last_teacher.student_id[1:])
                    new_id_num = last_id_num + 1
                except (ValueError, IndexError):
                    new_id_num = 1
            else:
                new_id_num = 1
            self.student_id = f"T{new_id_num:04d}"
        
        elif self.rol == self.Role.TYUTOR:
            # Eng oxirgi TYUTORni topamiz
            last_tyutor = StudentProfile.objects.filter(rol=self.Role.TYUTOR).order_by('student_id').last()
            if last_tyutor and last_tyutor.student_id:
                try:
                    last_id_num = int(last_tyutor.student_id[1:])
                    new_id_num = last_id_num + 1
                except (ValueError, IndexError):
                    new_id_num = 1
            else:
                new_id_num = 1
            self.student_id = f"C{new_id_num:04d}"
        
        # Agar rol ADMIN bo'lsa, unga student_id tayinlanmaydi

    # Asosiy save metodini chaqirib, barcha o'zgarishlarni saqlaymiz
    super().save(*args, **kwargs)
    
    def is_tyutor(self):
        return self.rol == self.Role.TYUTOR
    
    def get_assigned_groups(self):
        """Tyutor uchun ajratilgan guruhlarni qaytaradi"""
        if self.is_tyutor():
            return self.assigned_groups.all()
        return []