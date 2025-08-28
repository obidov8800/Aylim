# tests/models.py
from django.db import models
from users.models import StudentProfile
from django.utils import timezone
import datetime
class Group(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Guruh nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"

class TestSchedule(models.Model):
    author = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, related_name='created_tests', verbose_name="Muallif")
    title = models.CharField(max_length=255, verbose_name='Test sarlavhasi')
    tavsif = models.TextField(blank=True, null=True, verbose_name="Tavsif", default="") # Misol: matn uchun bo'sh qator
    davomiyligi = models.IntegerField(default=0, verbose_name="Davomiyligi (daqiqa)") # Misol: son uchun 0
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='test_schedules', verbose_name='Guruh')
    num_questions = models.PositiveIntegerField(default=0, verbose_name='Savollar soni') # Misol: son uchun 0

    # test_date, start_time, end_time uchun default qiymatlar
    test_date = models.DateField(verbose_name='Test sanasi', default=datetime.date.today) # Bugungi sana
    start_time = models.TimeField(verbose_name='Boshlanish vaqti', default=datetime.time(9, 0)) # Soat 09:00
    end_time = models.TimeField(verbose_name='Tugash vaqti', default=datetime.time(10, 0)) # Soat 10:00

    is_active = models.BooleanField(default=True, verbose_name='Aktiv')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Test Jadvali"
        verbose_name_plural = "Test Jadvallari"
        ordering = ['test_date', 'start_time']

class Question(models.Model):
    test_schedule = models.ForeignKey(TestSchedule, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(verbose_name="Savol matni")

    def __str__(self):
        return self.question_text[:50]
    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_options')
    answer_text = models.CharField(max_length=500, verbose_name="Javob matni")
    is_correct = models.BooleanField(default=False, verbose_name="To'g'ri javob")

    def __str__(self):
        return f"{self.answer_text} ({'To`g`ri' if self.is_correct else 'Noto`g`ri'})"
    class Meta:
        verbose_name = "Javob Varianti"
        verbose_name_plural = "Javob Variantlari"
        
class TestResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(TestSchedule, on_delete=models.CASCADE, related_name='results')
    # ### TUZATISH: Maydon turi o'zgartirildi ###
    score = models.FloatField(default=0, verbose_name="To'plangan ball")
    completion_time = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=50, blank=True, null=True, verbose_name="Baho")
    grade_color = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.score >= 90:
            self.grade = 'A\'lo (5)'
            self.grade_color = '#28a745'
        elif self.score >= 80:
            self.grade = 'Yaxshi (4)'
            self.grade_color = '#0dcaf0'
        elif self.score >= 70:
            self.grade = 'Qoniqarli (3)'
            self.grade_color = '#ffc107'
        else:
            self.grade = 'Qoniqarsiz (2)'
            self.grade_color = '#dc3545'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.test.title}: {self.score}"
    class Meta:
        verbose_name = "Test Natijasi"
        verbose_name_plural = "Test Natijalari"

class Bildirishnoma(models.Model):
    user = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    matn = models.TextField("Matn")
    yaratilgan_sana = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField("O'qilgan", default=False)

    def __str__(self):
        return f"{self.user.username} uchun bildirishnoma"
    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"

class StudentAnswer(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # TUZATISH: Talaba javob bermagan holatlar uchun null=True, blank=True qo'shildi
    selected_answer = models.ForeignKey(AnswerOption, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if self.selected_answer:
            return f"{self.question.question_text[:30]} - {self.selected_answer.answer_text[:30]}"
        return f"{self.question.question_text[:30]} - (Javob berilmagan)"
        
    class Meta:
        verbose_name = "Talabaning javobi"
        verbose_name_plural = "Talabalarning javoblari"

class Fan(models.Model):
    nomi = models.CharField(max_length=100, unique=True, verbose_name="Fan nomi")

    def __str__(self):
        return self.nomi
    class Meta:
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"


class DarsJadvali(models.Model):
    fan = models.ForeignKey(Fan, on_delete=models.CASCADE, verbose_name="Fan")
    guruh = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Guruh")
    oqtuvchi = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'rol': 'PEDAGOG'}, verbose_name="O'qituvchi")
    xona = models.CharField(max_length=50, null=True, blank=True, verbose_name="Xona")
    izoh = models.TextField(blank=True, null=True, verbose_name="Izoh")  # Yangi maydon qo'shildi
    boshlanish_vaqti = models.TimeField(verbose_name="Boshlanish vaqti")
    tugash_vaqti = models.TimeField(verbose_name="Tugash vaqti")
    start_date = models.DateField(verbose_name="Boshlanish sanasi")
    end_date = models.DateField(verbose_name="Tugash sanasi")

    def __str__(self):
        return f"{self.guruh.name} - {self.fan.nomi} ({self.start_date})"

    class Meta:
        verbose_name = "Dars Jadvali"
        verbose_name_plural = "Dars Jadvallari"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', '+'),
        ('absent', '-'),
        ('partial', 'Qisman'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(verbose_name="Sana")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    missed_lessons = models.PositiveIntegerField(null=True, blank=True, verbose_name="Qoldirilgan darslar")
    total_lessons = models.PositiveIntegerField(null=True, blank=True, verbose_name="Jami darslar")

    class Meta:
        unique_together = ('student', 'date')
        verbose_name = "Davomat Yozuvi"
        verbose_name_plural = "Davomat Yozuvlari"
        
        # YANGI RUXSATNOMA:
        permissions = [
            ("can_manage_attendance", "Can manage student attendance"),
        ]


    # __STR__ METODI YANGILANDI
    def __str__(self):
        if self.status == 'partial':
            return f"{self.missed_lessons or '?'}/{self.total_lessons or '?'}"
        # Aks holda, faqat belgisini qaytaradi ('+' yoki '-')
        return self.get_status_display()
