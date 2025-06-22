from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test # user_passes_test ni qo'shamiz
from django.contrib import messages
from django.utils import timezone
from .models import TestSchedule, Question, AnswerOption, TestResult, Group
from users.models import StudentProfile # StudentProfile ni import qilishni unutmang
from .forms import ImportQuestionsForm
import pandas as pd
import docx
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
# PDF generatsiya qilish uchun kerakli importlar
from django.http import HttpResponse # Bu yangi import
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape # landscape ni qo'shdik gorizontal PDF uchun
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch # inch birligini qo'shdik
from django.forms import formset_factory # import qiling
from .forms import TestScheduleForm, AnswerFormSet
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django import forms
import random # Fayl boshiga import qiling
from .models import TestSchedule, TestResult, Question, StudentAnswer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django import forms
from django.forms import inlineformset_factory
from django.db import transaction
from collections import defaultdict
import re
import docx
import pandas as pd
from io import BytesIO
from django.http import JsonResponse
import calendar
from datetime import date, timedelta
from .models import TestSchedule, Question, AnswerOption, Group, TestResult, StudentAnswer, Bildirishnoma, DarsJadvali, AttendanceRecord
from .forms import TestScheduleForm, AnswerFormSet, ImportQuestionsForm
# Testlar ro'yxatini ko'rsatish view'i
def is_teacher(user):
    return user.is_authenticated and (user.rol == 'PEDAGOG' or user.is_staff)

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
def test_list_view(request):
    # Bu funksiya talabaga uning guruhi uchun aktiv testlarni ko'rsatadi
    student = request.user
    active_tests = TestSchedule.objects.filter(group=student.group, is_active=True)
    test_data = []

    for test in active_tests:
        has_taken = TestResult.objects.filter(student=student, test=test).exists()
        result_id = None
        if has_taken:
            result_id = TestResult.objects.get(student=student, test=test).id
        
        test_data.append({'test': test, 'has_taken': has_taken, 'result_id': result_id})

    context = {'test_data': test_data, 'active_page': 'testlar'}
    return render(request, 'tests/test_list.html', context)


@login_required
def take_test_view(request, test_id):
    test = get_object_or_404(TestSchedule, id=test_id)
    student = request.user

    if TestResult.objects.filter(student=student, test=test).exists():
        messages.warning(request, "Siz bu testni allaqachon topshirgansiz.")
        return redirect('tests:test_list')

    # Savollarni tasodifiy tanlash
    all_questions = list(test.questions.all())
    num_to_select = min(test.num_questions, len(all_questions))
    
    # Agar savollar yetarli bo'lmasa, mavjud barchasini oladi
    if len(all_questions) < num_to_select:
        num_to_select = len(all_questions)
        
    random_questions = random.sample(all_questions, num_to_select)

    if request.method == 'POST':
        correct_answers_count = 0
        result = TestResult.objects.create(student=student, test=test, score=0)

        for question in random_questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                selected_answer = get_object_or_404(AnswerOption, id=selected_answer_id)
                StudentAnswer.objects.create(test_result=result, question=question, selected_answer=selected_answer)
                if selected_answer.is_correct:
                    correct_answers_count += 1
        
        # 100-ballik tizimda hisoblash
        score = round((100 / num_to_select) * correct_answers_count) if num_to_select > 0 else 0
        result.score = score
        result.save()

        return redirect('tests:test_result_detail', result_id=result.id)

    context = {'test': test, 'questions': random_questions, 'active_page': 'testlar'}
    return render(request, 'tests/take_test.html', context)


@login_required
def test_result_detail_view(request, result_id):
    result = get_object_or_404(TestResult, id=result_id, student=request.user)
    student_answers = {sa.question_id: sa.selected_answer for sa in result.student_answers.all()}
    
    # Natijalarni tayyorlash
    detailed_results = []
    # TestResult bilan bog'liq bo'lgan savollarni olish
    questions_in_result = Question.objects.filter(id__in=student_answers.keys())

    for question in questions_in_result:
        detailed_results.append({
            'question': question,
            'all_options': question.answer_options.all(),
            'selected_answer': student_answers.get(question.id)
        })

    context = {'result': result, 'detailed_results': detailed_results, 'active_page': 'testlar'}
    return render(request, 'tests/test_result_detail.html', context)

@user_passes_test(is_admin) # Faqat adminlar kirishi mumkin
def export_results_pdf_view(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="test_natijalari.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4)) # Gorizontal A4 o'lchami
    styles = getSampleStyleSheet()
    story = []

    # Sarlavha
    story.append(Paragraph("Umumiy Test Natijalari Ro'yxati", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Ma'lumotlar bazasidan barcha natijalarni olish
    # StudentProfile modelidagi 'full_name', 'passport_number', 'phone_number' maydonlaridan foydalanamiz
    results = TestResult.objects.all().order_by('student__group__name', 'student__full_name', 'test__title')

    if not results:
        story.append(Paragraph("Hech qanday test natijalari topilmadi.", styles['Normal']))
    else:
        # Jadval ustunlari
        data = [['F.I.Sh.', 'Pasport', 'Telefon', 'Guruh', 'Test nomi', 'Ball', 'Baho', 'Topshirilgan vaqt']]

        for res in results:
            student_full_name = res.student.full_name
            student_passport = res.student.passport_number
            student_phone = res.student.phone_number
            student_group = res.student.group.name if res.student.group else 'Noma\'lum'
            test_title = res.test.title
            score = str(res.score)
            grade = res.grade
            completion_time = res.completion_time.strftime("%Y-%m-%d %H:%M")

            data.append([
                student_full_name,
                student_passport,
                student_phone,
                student_group,
                test_title,
                score,
                grade,
                completion_time
            ])

        # Jadvalni yaratish
        table = Table(data)

        # Jadval stili
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen), # Sarlavha qatori foni
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black), # Sarlavha matni rangi

            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), # Barcha matnni markazga
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Sarlavha shrifti
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            ('BACKGROUND', (0, 1), (-1, -1), colors.beige), # Qolgan qatorlar foni
            ('GRID', (0, 0), (-1, -1), 1, colors.black), # Ramka
            ('BOX', (0, 0), (-1, -1), 1, colors.black), # Tashqi ramka
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))

        # Jadval ustunlari kengligini sozlash (qulay ko'rinishi uchun)
        # A4 landscape 841.89 x 595.27 points
        col_widths = [2.2*inch, 1*inch, 1.2*inch, 1*inch, 1.8*inch, 0.5*inch, 0.5*inch, 1.2*inch]
        table._argW = col_widths

        story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def is_teacher(user):
    """
    Foydalanuvchi Pedagog yoki Admin ekanligini tekshiradi.
    """
    return user.is_authenticated and (user.rol == 'PEDAGOG' or user.is_staff)

@user_passes_test(is_teacher)
def import_questions_from_file_view(request, test_id):
    test_schedule = get_object_or_404(TestSchedule, id=test_id)

    if request.method == 'POST':
        form = ImportQuestionsForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            questions_count = 0

            try:
                # --- .DOCX fayllar uchun mantiq ---
                if uploaded_file.name.endswith('.docx'):
                    document = docx.Document(uploaded_file)
                    full_text = "\n".join([para.text for para in document.paragraphs])
                    
                    question_blocks = re.split(r'\n(?=\d+\.\s)', full_text.strip())

                    for block in question_blocks:
                        if not block.strip():
                            continue

                        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
                        
                        question_match = re.match(r'^\d+\.\s*(.*)', lines[0])
                        if not question_match:
                            continue
                        question_text = question_match.group(1).strip()
                        
                        question_obj = Question.objects.create(test_schedule=test_schedule, question_text=question_text)
                        
                        options = {}
                        correct_answer_char = ''
                        for line in lines[1:]:
                            option_match = re.match(r'^([a-d]|A-D)\)\s*(.*)', line)
                            if option_match:
                                # XATOLIK TUZATILDI: toUpperCase() -> upper()
                                char = option_match.group(1).upper()
                                text = option_match.group(2).strip()
                                options[char] = text
                            
                            correct_match = re.search(r'To‘g‘ri javob:\s*([A-D])', line, re.IGNORECASE)
                            if correct_match:
                                correct_answer_char = correct_match.group(1).upper()

                        for char, text in options.items():
                            AnswerOption.objects.create(
                                question=question_obj,
                                answer_text=text,
                                is_correct=(char == correct_answer_char)
                            )
                        questions_count += 1
                
                # --- Excel/CSV fayllar uchun eski mantiq ---
                elif uploaded_file.name.endswith(('.xls', '.xlsx', '.csv')):
                    # ... excel/csv uchun mantiq ...
                    pass

                else:
                    messages.error(request, "Fayl formati noto'g'ri. Faqat .docx, .xlsx, .xls, .csv fayllari qabul qilinadi.")
                    return render(request, 'tests/import_questions.html', {'form': form, 'test_schedule': test_schedule})

                # Testning savollar sonini yangilash
                test_schedule.num_questions = test_schedule.questions.count()
                test_schedule.save()

                messages.success(request, f"{questions_count} ta savol va ularning javoblari muvaffaqiyatli import qilindi!")
                return redirect('tests:teacher_test_list')

            except Exception as e:
                messages.error(request, f"Faylni qayta ishlashda xatolik yuz berdi: {e}")
    else:
        form = ImportQuestionsForm()

    context = {
        'form': form,
        'test_schedule': test_schedule,
        'title': f"'{test_schedule.title}' testi uchun savollarni import qilish",
        'active_page': 'mening_testlarim',
    }
    return render(request, 'tests/import_questions.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_test_list_view(request):
    # Faqat shu o'qituvchi yaratgan testlarni ko'rsatish (hozircha barcha testlar)
    tests = TestSchedule.objects.all().order_by('-open_time')
    return render(request, 'tests/teacher_test_list.html', {'tests': tests, 'active_page': 'mening_testlarim'})

# tests/views.py


@login_required
@user_passes_test(is_teacher)
def delete_test_view(request, test_id):
    test = get_object_or_404(TestSchedule, id=test_id)
    if request.method == 'POST':
        test.delete()
        messages.success(request, f"'{test.title}' testi muvaffaqiyatli o'chirildi.")
        return redirect('tests:teacher_test_list')
    return render(request, 'tests/delete_test_confirm.html', {'test': test})

@login_required
@user_passes_test(is_teacher)
def test_constructor_view(request, test_id=None):
    if test_id:
        instance = get_object_or_404(TestSchedule, id=test_id)
        title = "Test Konstruktori: Tahrirlash"
    else:
        # Yangi test yaratishda muallifni belgilash
        instance = TestSchedule(author=request.user if request.user.is_authenticated else None)
        title = "Test Konstruktori: Yaratish"

    QuestionFormSet = inlineformset_factory(
        TestSchedule, Question, fields=('question_text',),
        extra=1, can_delete=True,
        widgets={'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2})}
    )
    import_form = ImportQuestionsForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_test':
            form = TestScheduleForm(request.POST, instance=instance)
            question_formset = QuestionFormSet(request.POST, instance=instance, prefix='questions')

            if form.is_valid() and question_formset.is_valid():
                # ... (saqlash logikasi avvalgidek) ...
                messages.success(request, "Test muvaffaqiyatli saqlandi.")
                return redirect('tests:edit_test', test_id=form.instance.id)
            else:
                messages.error(request, "Formani to'ldirishda xatoliklar mavjud.")
        
        elif action == 'import_questions' and instance.pk:
            # ... (import logikasi avvalgidek) ...
            return redirect('tests:edit_test', test_id=instance.id)

    # BU QISM `if request.method == 'POST'` DAN TASHQARIDA BO'LISHI KERAK
    form = TestScheduleForm(instance=instance)
    question_formset = QuestionFormSet(instance=instance, prefix='questions')
    for q_form in question_formset:
        q_form.answer_formset = AnswerFormSet(instance=q_form.instance, prefix=f'answers_{q_form.prefix}')

    context = {
        'form': form,
        'question_formset': question_formset,
        'import_form': import_form,
        'title': title,
        'test': instance,
        'active_page': 'mening_testlarim',
    }
    # FUNKSIYANING ENG OXIRGI QATORI
    return render(request, 'tests/test_constructor.html', context)

@login_required
def timetable_view(request):
    user = request.user
    # Hafta kunlari to'g'ri tartibda chiqishi uchun ro'yxat
    days = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba']
    full_timetable = []

    # Agar foydalanuvchi biror guruhga a'zo bo'lsa
    if hasattr(user, 'group') and user.group:
        # Har bir kun uchun darslarni alohida olib, ro'yxatga qo'shamiz
        for day in days:
            lessons_for_day = DarsJadvali.objects.filter(guruh=user.group, hafta_kuni=day).order_by('boshlanish_vaqti')
            full_timetable.append({'day': day, 'lessons': lessons_for_day})

    context = {
        'full_timetable': full_timetable,
        'active_page': 'dars_jadvali', # Menyuda aktiv qilish uchun
    }
    return render(request, 'tests/timetable.html', context)

@login_required
def attendance_student_view(request):
    student = request.user
    today = date.today()

    UZBEK_MONTHS = [
        "", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
    ]
    UZBEK_WEEKDAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month
    
    current_month_date = date(year, month, 1)

    cal = calendar.Calendar()
    month_weeks = cal.monthdatescalendar(year, month)
    
    records = AttendanceRecord.objects.filter(
        student=student, 
        date__year=year,
        date__month=month
    )
    
    # Davomatni sana bo'yicha tez topish uchun lug'at yaratamiz
    attendance_map = {rec.date: rec for rec in records}

    # Oldingi va keyingi oylar uchun linklar
    prev_month_date = current_month_date - timedelta(days=1)
    next_month_date = (current_month_date + timedelta(days=32)).replace(day=1)

    context = {
        'active_page': 'davomat',
        'month_weeks': month_weeks,
        'attendance_map': attendance_map,
        'current_month_num': month,
        'current_month_str': f"{UZBEK_MONTHS[month]}, {year}",
        'prev_month_url': f'?year={prev_month_date.year}&month={prev_month_date.month}',
        'next_month_url': f'?year={next_month_date.year}&month={next_month_date.month}',
    }
    return render(request, 'tests/attendance_student.html', context)

@login_required
@user_passes_test(is_teacher)
def attendance_management_view(request):
    groups = Group.objects.all()
    context = {
        'groups': groups,
        'active_page': 'davomat_boshqarish',
    }
    return render(request, 'tests/attendance_management.html', context)

@login_required
def get_attendance_data_view(request):
    group_id = request.GET.get('group_id')
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    week_num = int(request.GET.get('week', 0))

    students = StudentProfile.objects.filter(group_id=group_id, rol='TALABA').order_by('full_name')
    cal = calendar.Calendar()
    month_weeks = cal.monthdatescalendar(year, month)

    if week_num >= len(month_weeks): week_num = 0
    current_week_dates = month_weeks[week_num]

    records = AttendanceRecord.objects.filter(
        student__in=students, 
        date__in=current_week_dates
    )
    
    attendance_map = {rec.date.isoformat(): str(rec) for rec in records}

    student_data = []
    for student in students:
        row = {'id': student.id, 'full_name': student.full_name, 'dates': []}
        for d in current_week_dates:
            status = attendance_map.get(d.isoformat(), '')
            row['dates'].append({
                'date': d.isoformat(),
                'day': d.day,
                'is_current_month': d.month == month,
                'status': status
            })
        student_data.append(row)

    data = {
        'students_data': student_data,
        'week_days': [{'date': d.isoformat(), 'day': d.day, 'is_current_month': d.month == month} for d in current_week_dates],
        'week_num': week_num,
        'total_weeks': len(month_weeks),
        'month_name': calendar.month_name[month],
        'year': year,
    }
    return JsonResponse(data)


@login_required
def get_attendance_data_view(request):
    group_id = request.GET.get('group_id')
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    week_num = int(request.GET.get('week', 0))

    students = StudentProfile.objects.filter(group_id=group_id, rol='TALABA').order_by('full_name')
    cal = calendar.Calendar()
    month_weeks = cal.monthdatescalendar(year, month)

    if week_num >= len(month_weeks): week_num = 0
    current_week_dates = month_weeks[week_num]
    
    records = AttendanceRecord.objects.filter(student__in=students, date__in=current_week_dates)
    
    attendance_map = {}
    for rec in records:
        key = (rec.student_id, rec.date.isoformat())
        attendance_map[key] = str(rec) # Modelning __str__ metodidan foydalanamiz

    student_data = []
    for student in students:
        row = {'id': student.id, 'full_name': student.full_name, 'dates': []}
        for d in current_week_dates:
            status = attendance_map.get((student.id, d.isoformat()), '')
            row['dates'].append({'date': d.isoformat(), 'day': d.day, 'is_current_month': d.month == month, 'status': status})
        student_data.append(row)

    data = {
        'students_data': student_data,
        'week_days': [{'date': d.isoformat(), 'day': d.day, 'is_current_month': d.month == month} for d in current_week_dates],
        'week_num': week_num,
        'total_weeks': len(month_weeks),
        'month_name': calendar.month_name[month],
        'year': year,
    }
    return JsonResponse(data)

@login_required
@user_passes_test(is_teacher)
def update_attendance_view(request):
    if request.method == 'POST':
        student = get_object_or_404(StudentProfile, id=request.POST.get('student_id'))
        att_date = date.fromisoformat(request.POST.get('date'))
        status = request.POST.get('status')
        
        # Agar status "delete" bo'lsa, yozuvni o'chiramiz
        if status == 'delete':
            AttendanceRecord.objects.filter(student=student, date=att_date).delete()
            return JsonResponse({'success': True, 'display_status': ''})

        # Aks holda, yozuvni yaratamiz yoki yangilaymiz
        defaults = {'status': status}
        if status == 'partial':
            defaults['missed_lessons'] = request.POST.get('missed_lessons')
            defaults['total_lessons'] = request.POST.get('total_lessons')
        else:
            defaults['missed_lessons'] = None
            defaults['total_lessons'] = None
            
        record, created = AttendanceRecord.objects.update_or_create(
            student=student, date=att_date,
            defaults=defaults
        )
        return JsonResponse({'success': True, 'display_status': str(record)})
        
    return JsonResponse({'success': False})