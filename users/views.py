# users/views.py

from django.shortcuts import render, redirect # render va redirect funksiyalari uchun
from django.contrib.auth import login, authenticate, logout # Tizimga kirish/chiqish uchun
from django.contrib.auth.forms import AuthenticationForm # Standart login formasi uchun
from django.contrib.auth.decorators import login_required # Kirish talab qilinadigan view'lar uchun
from django.contrib import messages # Xabarnomalar uchun
from .forms import StudentRegistrationForm # Keyinroq yaratiladigan custom ro'yxatdan o'tish formasi uchun
from .models import StudentProfile # StudentProfile modelimiz uchun
from tests.models import TestResult
from .forms import ProfileUpdateForm 
from tests.models import Bildirishnoma

# Foydalanuvchini ro'yxatdan o'tkazish view'i
def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            try:
                message_text = (f"Hurmatli {user.full_name}, tizimdan muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
                                f"Sizning ID raqamingiz: {user.student_id}\n"
                                f"Login uchun ismingiz: {user.username}\n\n"
                                f"Parol: (Siz ro'yxatdan o'tishda o'zingiz kiritgan parol)")

                # ### TUZATISH: Maydon nomi 'matn' ga o'zgartirildi ###
                Bildirishnoma.objects.create(user=user, matn=message_text)

            except Exception as e:
                print(f"Bildirishnoma yaratishda xatolik: {e}")

            login(request, user)
            messages.success(request, "Siz muvaffaqiyatli ro'yxatdan o'tdingiz!")
            return redirect('users:profile')
    else:
        form = StudentRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sizning profilingiz muvaffaqiyatli yangilandi!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'users/profile_update.html', {'form': form, 'active_page': 'profil'})

# Foydalanuvchini tizimga kiritish view'i
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff:
                    return redirect('/admin/')
                elif user.rol == StudentProfile.Role.PEDAGOG:
                    return redirect('tests:teacher_test_list')
                else:
                    return redirect('tests:test_list')
            else:
                messages.error(request, "Foydalanuvchi nomi yoki parol noto'g'ri.")
        else:
            messages.error(request, "Iltimos, maydonlarni to'g'ri to'ldiring.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

# Foydalanuvchini tizimdan chiqarish view'i
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('users:login')

@login_required
def profile_view(request):
    student_profile = request.user
    student_results = TestResult.objects.filter(student=student_profile).order_by('-completion_time')
    context = {
        'student_profile': student_profile,
        'student_results': student_results,
        'active_page': 'profil',
    }
    return render(request, 'users/profile.html', context)

# Asosiy sahifa view'i
@login_required
def home_view(request):
    # Bu yerda siz foydalanuvchi tizimga kirgandan keyin ko'radigan ma'lumotlarni joylashtirishingiz mumkin.
    # Masalan, testlar ro'yxatiga yo'naltirish:
    return redirect('tests:test_list')

@login_required
def notification_list_view(request):
    notifications = Bildirishnoma.objects.filter(user=request.user).order_by('-created_at')
    
    # O'qilmagan bildirishnomalarni "o'qilgan" deb belgilash
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
        'active_page': 'bildirishnomalar',
    }
    return render(request, 'tests/notification_list.html', context)