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
from django.contrib.auth import login
# Foydalanuvchini ro'yxatdan o'tkazish view'i
def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # 1-QADAM: Parolni ochiq matn ko'rinishida vaqtinchalik saqlab olish
            plain_password = form.cleaned_data.get('password')

            # 2-QADAM: Foydalanuvchini bazaga saqlash, lekin parolni hali heshlamasdan
            # form.save(commit=False) metodi bazaga saqlamasdan obyekt yaratib beradi
            user = form.save(commit=False)
            
            # 3-QADAM: Endi parolni heshlab, foydalanuvchiga o'rnatish
            user.set_password(plain_password)
            
            # 4-QADAM: Barcha o'zgarishlar bilan foydalanuvchini bazaga to'liq saqlash
            user.save()
            
            # Guruhlarni saqlash (agar ManyToMany maydoni bo'lsa)
            form.save_m2m()

            # 5-QADAM: Ochiq paroldan foydalanib bildirishnoma yaratish
            message_text = (
                f"Hurmatli {user.full_name}, tizimdan muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
                f"Sizning ID raqamingiz: {user.student_id}\n"
                f"Parolingiz: {plain_password}"  # <-- O'ZGARTIRILGAN QATOR
            )
            Bildirishnoma.objects.create(user=user, matn=message_text)
            
            # Ro'yxatdan o'tgandan so'ng foydalanuvchini avtomatik tizimga kiritish
            login(request, user)

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
                
                # Foydalanuvchi roliga qarab yo'naltiramiz
                if user.rol == StudentProfile.Role.PEDAGOG:
                    # Pedagog bo'lsa teacher dashboardga
                    return redirect('tests:teacher_test_list')
                elif user.rol == StudentProfile.Role.TYUTOR:
                    # Tyutor bo'lsa tyutor dashboardga
                    return redirect('/mumiyo/')
                elif user.is_staff or user.is_superuser:
                    # Admin yoki staff bo'lsa admin panelga
                    return redirect('/mumiyo/')
                else:
                    # Talaba yoki boshqa roldagi foydalanuvchilar
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