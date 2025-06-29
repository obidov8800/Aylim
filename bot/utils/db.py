# bot/utils/db.py

import random
import string
from asgiref.sync import sync_to_async
from django.db import models # <-- MUHIM: YETISHMAYOTGAN IMPORT QO'SHILDI
from users.models import StudentProfile
from tests.models import DarsJadvali, Bildirishnoma, TestResult

@sync_to_async
def get_user_by_telegram_id(telegram_id: int):
    """ Telegram ID orqali foydalanuvchini va unga bog'liq guruhni bitta so'rovda topadi """
    return StudentProfile.objects.select_related('group').filter(telegram_id=telegram_id).first()

@sync_to_async
def find_user_by_username(username: str):
    """ Saytdagi logini (username) orqali foydalanuvchini topadi """
    try:
        return StudentProfile.objects.get(username=username)
    except StudentProfile.DoesNotExist:
        return None
        
@sync_to_async
def get_user_by_pk(user_pk: int):
    """ Foydalanuvchini uning primary key (ID) raqami orqali topadi """
    try:
        # Bu yerda ham guruh ma'lumotini oldindan olamiz, har ehtimolga qarshi
        return StudentProfile.objects.select_related('group').get(pk=user_pk)
    except StudentProfile.DoesNotExist:
        return None

@sync_to_async
def set_verification_code(user_pk: int) -> str:
    """ Foydalanuvchi uchun tasdiqlash kodini yaratadi va saqlaydi """
    code = ''.join(random.choices(string.digits, k=6))
    StudentProfile.objects.filter(pk=user_pk).update(telegram_verification_code=code)
    return code

@sync_to_async
def link_telegram_account(user_pk: int, telegram_id: int):
    """ Profilni Telegram akkauntga bog'laydi va tasdiqlash kodini tozalaydi """
    StudentProfile.objects.filter(pk=user_pk).update(
        telegram_id=telegram_id,
        telegram_verification_code=None
    )

@sync_to_async
def get_user_schedule(user: StudentProfile):
    """ 
    Foydalanuvchining guruhi uchun dars jadvalini oladi.
    BOG'LIQ BARCHA MODELLARNI (fan, oqtuvchi) BITTA SO'ROVDA YUKLAYDI.
    """
    if not user.group:
        return None
        
    # YAKUNIY YECHIM: select_related orqali barcha kerakli ma'lumotlarni oldindan yuklab olamiz
    schedule = DarsJadvali.objects.filter(
        guruh=user.group
    ).select_related(
        'fan', 
        'oqtuvchi'
    ).order_by('hafta_kuni', 'boshlanish_vaqti')
    
    return list(schedule)

@sync_to_async
def get_user_notifications(user: StudentProfile):
    """ 
    Foydalanuvchi uchun shaxsiy xabarnomalarni oladi.
    Modelda guruh yo'qligi uchun faqat user bo'yicha filter qilinadi.
    """
    notifications = Bildirishnoma.objects.filter(user=user).order_by('-yaratilgan_sana')[:10]
    return list(notifications)

@sync_to_async
def set_password_reset_code(user_pk: int) -> str:
    """ Foydalanuvchi uchun parolni tiklash kodini yaratadi va saqlaydi """
    code = ''.join(random.choices(string.digits, k=6))
    user = StudentProfile.objects.get(pk=user_pk)
    user.password_reset_code = code
    user.save()
    return code

@sync_to_async
def reset_user_password(user_pk: int, new_password: str):
    """ Foydalanuvchining parolini yangilaydi """
    user = StudentProfile.objects.get(pk=user_pk)
    user.set_password(new_password)  # Parolni to'g'ri hash'lab saqlaydi
    user.save()

@sync_to_async
def get_user_test_results(user: StudentProfile):
    """ Foydalanuvchining test natijalarini oladi """
    results = TestResult.objects.filter(
        student=user
    ).select_related(
        'test'  # XATO TUZATILDI
    ).order_by('-completion_time')[:10]
    return list(results)