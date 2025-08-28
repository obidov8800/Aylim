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
from .forms import TestScheduleForm, QuestionForm, AnswerFormSet, ImportQuestionsForm
# Testlar ro'yxatini ko'rsatish view'i
def is_student(user):  # <--- SHU FUNKSIYANI QO'SHING
    """
    Foydalanuvchi Talaba ekanligini tekshiradi.
    """
    return user.is_authenticated and hasattr(user, 'rol') and user.rol == 'TALABA'

def is_teacher(user):
    return user.is_authenticated and (user.rol == 'PEDAGOG' or user.is_staff)

def is_admin(user):
    return user.is_authenticated and user.is_staffff

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
@user_passes_test(is_student)
def take_test_view(request, test_id):
    test = get_object_or_404(TestSchedule, id=test_id)
    student = request.user

    if TestResult.objects.filter(student=student, test=test).exists():
        messages.warning(request, "Siz bu testni allaqachon topshirgansiz.")
        return redirect('tests:test_list')

    # POST so'rovini qayta ishlash (Testni yakunlash)
    if request.method == 'POST':
        # YECHIM: Savollar ro'yxatini foydalanuvchi sessiyasidan olamiz
        question_ids = request.session.get(f'test_attempt_{test_id}')
        if not question_ids:
            messages.error(request, "Test seansida xatolik yuz berdi. Iltimos, qaytadan boshlang.")
            return redirect('tests:test_list')
        
        # Sessiyadagi IDlar bo'yicha aniq o'sha savollarni olamiz
        questions_in_attempt = list(Question.objects.filter(id__in=question_ids))
        
        # Tekshiruv: Barcha savollarga javob berilganmi?
        all_answered = True
        for question in questions_in_attempt:
            if f'question_{question.id}' not in request.POST:
                all_answered = False
                break
        
        if not all_answered:
            messages.error(request, "Iltimos, barcha savollarga javob bering. Javob berilmagan savollar qizil rangda belgilandi.")
            # Xatolik yuz bersa ham, belgilangan javoblarni saqlab qolish uchun
            context = {
                'test': test,
                'questions': questions_in_attempt, # Qayta o'sha savollarni ko'rsatamiz
                'submitted_answers': request.POST, # Kiritilgan javoblarni qaytaramiz
                'unanswered_question_ids': [q.id for q in questions_in_attempt if f'question_{q.id}' not in request.POST],
                'active_page': 'testlar'
            }
            return render(request, 'tests/take_test.html', context)
        
        # Agar hamma narsa to'g'ri bo'lsa, natijani hisoblaymiz
        correct_answers_count = 0
        result = TestResult.objects.create(student=student, test=test, score=0)
        with transaction.atomic():
            for question in questions_in_attempt:
                selected_answer_id = request.POST.get(f'question_{question.id}')
                selected_answer = get_object_or_404(AnswerOption, id=selected_answer_id)
                if selected_answer.is_correct:
                    correct_answers_count += 1
                StudentAnswer.objects.create(test_result=result, question=question, selected_answer=selected_answer)

        score = round((100 / len(questions_in_attempt)) * correct_answers_count) if questions_in_attempt else 0
        result.score = score
        result.save()
        
        # Ishlatilgan sessiyani tozalaymiz
        del request.session[f'test_attempt_{test_id}']

        messages.success(request, f"Test yakunlandi! Natijangiz: {score} ball")
        return redirect('tests:test_result_detail', result_id=result.id)

    # GET so'rovi (Testni boshlash)
    else:
        all_questions = list(test.questions.all())
        if not all_questions:
            messages.error(request, "Ushbu testda hali savollar mavjud emas.")
            return redirect('tests:test_list')
        
        num_to_select = test.num_questions if 0 < test.num_questions <= len(all_questions) else len(all_questions)
        random_questions = random.sample(all_questions, num_to_select)
        
        # YECHIM: Tasodifiy tanlangan savollar ro'yxatini sessiyaga saqlab qo'yamiz
        request.session[f'test_attempt_{test_id}'] = [q.id for q in random_questions]

        context = {'test': test, 'questions': random_questions, 'active_page': 'testlar'}
        return render(request, 'tests/take_test.html', context)


@login_required
def test_result_detail_view(request, result_id):
    result = get_object_or_404(TestResult, id=result_id)
    
    if not request.user.is_staff and result.student != request.user:
        messages.error(request, "Sizga bu natijani ko'rishga ruxsat berilmagan.")
        return redirect('tests:test_list')

    student_answers_qs = result.student_answers.select_related('question', 'selected_answer').order_by('question_id')
    
    # ### YANGILIK: To'g'ri javoblar sonini hisoblash ###
    correct_answers_count = student_answers_qs.filter(selected_answer__is_correct=True).count()
    total_questions_in_attempt = student_answers_qs.count()

    detailed_results = []
    for answer_record in student_answers_qs:
        detailed_results.append({
            'question': answer_record.question,
            'options': answer_record.question.answer_options.all(),
            'selected_answer': answer_record.selected_answer,
        })

    context = {
        'result': result, 
        'detailed_results': detailed_results,
        'correct_answers_count': correct_answers_count,
        'total_questions_in_attempt': total_questions_in_attempt,
        'active_page': 'testlar'
    }
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



@login_required
@user_passes_test(is_teacher)
def import_questions_from_file_view(request, test_id):
    test_schedule = get_object_or_404(TestSchedule, id=test_id, author=request.user)

    if request.method == 'POST':
        form = ImportQuestionsForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            questions_added_count = 0
            questions_skipped_count = 0

            try:
                if not uploaded_file.name.endswith('.docx'):
                    messages.error(request, "Fayl formati noto'g'ri. Faqat .docx fayllari qabul qilinadi.")
                    return redirect('tests:import_questions', test_id=test_schedule.id)

                document = docx.Document(uploaded_file)
                full_text = "\n".join([para.text for para in document.paragraphs if para.text.strip()])
                question_blocks = re.split(r'\n(?=\d+\.\s)', full_text.strip())

                with transaction.atomic():
                    for block in question_blocks:
                        if not block.strip(): continue
                        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
                        question_match = re.match(r'^\d+\.\s*(.+)', lines[0])
                        if not question_match:
                            questions_skipped_count += 1
                            continue

                        question_text = question_match.group(1).strip()
                        options, correct_answer_char = {}, None
                        
                        for line in lines[1:]:
                            option_match = re.match(r'^\s*([A-D])\)\s*(.+)', line, re.IGNORECASE)
                            correct_match = re.search(r'To‘g‘ri javob:\s*([A-D])', line, re.IGNORECASE)
                            if option_match:
                                options[option_match.group(1).upper()] = option_match.group(2).strip()
                            elif correct_match:
                                correct_answer_char = correct_match.group(1).upper()

                        if not options or not correct_answer_char or correct_answer_char not in options:
                            questions_skipped_count += 1
                            continue

                        question_obj = Question.objects.create(test_schedule=test_schedule, question_text=question_text)
                        for char, text in options.items():
                            AnswerOption.objects.create(question=question_obj, answer_text=text, is_correct=(char == correct_answer_char))
                        questions_added_count += 1
                
                test_schedule.num_questions = test_schedule.questions.count()
                test_schedule.save()

                if questions_added_count > 0:
                    messages.success(request, f"{questions_added_count} ta savol muvaffaqiyatli import qilindi!")
                if questions_skipped_count > 0:
                    messages.warning(request, f"{questions_skipped_count} ta savol fayldagi format xatoligi tufayli o'tkazib yuborildi.")
                
                return redirect('tests:edit_test', test_id=test_schedule.id)

            except Exception as e:
                messages.error(request, f"Faylni qayta ishlashda kutilmagan xatolik yuz berdi: {e}")
                return redirect('tests:import_questions', test_id=test_schedule.id)
    else:
        form = ImportQuestionsForm()

    context = {
        'form': form,
        'test_schedule': test_schedule,
        'title': f"'{test_schedule.title}' testi uchun savollarni import qilish"
    }
    return render(request, 'tests/import_questions.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_test_list_view(request):
    # Faqat shu o'qituvchi yaratgan testlarni ko'rsatish (hozircha barcha testlar)
    tests = TestSchedule.objects.all().order_by('-test_date', '-start_time')
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
        test = get_object_or_404(TestSchedule, pk=test_id, author=request.user)
        title = "Testni tahrirlash"
    else:
        test = None
        title = "Yangi test yaratish"

    QuestionFormSet = inlineformset_factory(
        TestSchedule, Question, form=QuestionForm,
        extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = TestScheduleForm(request.POST, instance=test)
        
        # Yangi test bo'lsa, uni avval saqlab, ID olamiz
        if test is None:
            if form.is_valid():
                instance = form.save(commit=False)
                instance.author = request.user
                instance.save()
                messages.success(request, "Test yaratildi. Endi savollarni qo'shing.")
                return redirect('tests:edit_test', test_id=instance.id)
            # Agar form xato bo'lsa, `formset` bo'sh bo'ladi
            formset = QuestionFormSet(instance=test)
        
        # Mavjud test tahrirlanayotgan bo'lsa
        else:
            formset = QuestionFormSet(request.POST, instance=test, prefix='questions')
            if form.is_valid() and formset.is_valid():
                with transaction.atomic():
                    saved_test = form.save()
                    questions = formset.save() # Savollar saqlandi

                    all_answers_valid = True
                    for question in questions:
                        # Har bir savol uchun uning javob formsetini olamiz va tekshiramiz
                        answer_formset = AnswerFormSet(request.POST, instance=question, prefix=f'answers_{question.id}')
                        if not answer_formset.is_valid():
                            all_answers_valid = False
                            messages.error(request, f"'{question.question_text[:30]}...' savolining javoblarida xatolik bor. Iltimos, to'g'ri javobni belgilang.")
                            break
                    
                    if all_answers_valid:
                        # Agar barcha javoblar to'g'ri bo'lsa, ularni ham saqlaymiz
                        for question in questions:
                            answer_formset = AnswerFormSet(request.POST, instance=question, prefix=f'answers_{question.id}')
                            answer_formset.save()
                        messages.success(request, "Test muvaffaqiyatli saqlandi.")
                        return redirect('tests:edit_test', test_id=saved_test.id)
                    else:
                        transaction.set_rollback(True) # Xatolik bo'lsa, o'zgarishlarni bekor qilamiz
            else:
                messages.error(request, "Iltimos, formadagi xatoliklarni to'g'rilang.")

    else: # GET so'rovi (sahifani birinchi marta ochganda)
        form = TestScheduleForm(instance=test)
        formset = QuestionFormSet(instance=test, prefix='questions')

    # ### ENG ASOSIY TUZATISH: JAVOB VARIANTLARINI ANDOZAGA YUBORISH ###
    # Bu qism endi har doim, GET so'rovida ham, POST'dagi xatolikda ham ishlaydi
    for q_form in formset:
        if request.method == 'POST':
            # Agar POST'da xatolik bo'lsa, kiritilgan ma'lumotlarni yo'qotmasdan formsetni qayta yaratamiz
            q_form.answer_formset = AnswerFormSet(request.POST, instance=q_form.instance, prefix=f'answers_{q_form.instance.id}' if q_form.instance.pk else f'answers_new_{q_form.prefix}')
        else:
            # GET so'rovida oddiy formset yaratamiz
            q_form.answer_formset = AnswerFormSet(instance=q_form.instance, prefix=f'answers_{q_form.instance.id}' if q_form.instance.pk else f'answers_new_{q_form.prefix}')

    context = {
        'form': form,
        'question_formset': formset,
        'title': title,
        'test': test,
        'active_page': 'mening_testlarim',
    }
    return render(request, 'tests/test_constructor.html', context)


@login_required
def timetable_view(request):
    user = request.user
    days = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba']
    full_timetable = []
    hozirgi_sana = date.today()
    
    if hasattr(user, 'group') and user.group:
        # Hozirgi haftaning Dushanba va Shanba sanasini hisoblaymiz
        hafta_boshi = hozirgi_sana - timedelta(days=hozirgi_sana.weekday())
        hafta_oxiri = hafta_boshi + timedelta(days=5)
        
        # Guruh va joriy haftadagi darslarni olamiz
        all_lessons_for_user = DarsJadvali.objects.filter(
            guruh=user.group,
            start_date__lte=hafta_oxiri,
            end_date__gte=hafta_boshi
        ).order_by('boshlanish_vaqti')
        
        # Har bir hafta kuni uchun darslar ro'yxatini tuzamiz
        for day_index, day_name in enumerate(days):
            lessons_for_day = []
            current_day_date = hafta_boshi + timedelta(days=day_index)
            
            for lesson in all_lessons_for_user:
                # Dars joriy kunga to'g'ri keladimi tekshiramiz
                if lesson.start_date <= current_day_date <= lesson.end_date:
                    # Haftaning qaysi kuniga to'g'ri kelishini tekshiramiz
                    if current_day_date.weekday() == day_index:
                        lessons_for_day.append({
                            'lesson': lesson,
                            'date': current_day_date
                        })
            
            full_timetable.append({'day': day_name, 'lessons': lessons_for_day, 'date': current_day_date})

    context = {
        'full_timetable': full_timetable,
        'active_page': 'dars_jadvali',
    }
    return render(request, 'tests/timetable.html', context)

@login_required
@user_passes_test(is_student)  # is_student funksiyasi tepada e'lon qilingan bo'lishi kerak
def attendance_student_view(request):
    student = request.user
    today = date.today()

    UZBEK_MONTHS = [
        "", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
    ]

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month
    
    current_month_date = date(year, month, 1)

    cal = calendar.Calendar()
    month_weeks = cal.monthdatescalendar(year, month)
    
    first_day_of_cal = month_weeks[0][0]
    last_day_of_cal = month_weeks[-1][-1]
    records = AttendanceRecord.objects.filter(
        student=student, 
        date__range=(first_day_of_cal, last_day_of_cal)
    )
    
    attendance_map = {rec.date: rec for rec in records}

    # YECHIM: Ma'lumotlarni andoza uchun qulay 'calendar_data' formatiga o'tkazish
    calendar_data = []
    for week in month_weeks:
        week_data = []
        for day_date in week:
            week_data.append({
                'date': day_date,
                'record': attendance_map.get(day_date)
            })
        calendar_data.append(week_data)

    # Oldingi va keyingi oylar uchun linklar
    prev_month_date = current_month_date - timedelta(days=1)
    prev_month_url_params = f"?year={prev_month_date.year}&month={prev_month_date.month}"
    
    next_month_date = current_month_date + timedelta(days=32)
    next_month_date = next_month_date.replace(day=1)
    next_month_url_params = f"?year={next_month_date.year}&month={next_month_date.month}"

    context = {
        'active_page': 'davomat',
        'calendar_data': calendar_data,
        'current_month_num': month,
        'current_month_str': f"{UZBEK_MONTHS[month]}, {year}",
        'prev_month_url_params': prev_month_url_params,
        'next_month_url_params': next_month_url_params,
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

@login_required
def notification_list_view(request):
    # ### TUZATISH: Maydon nomi 'yaratilgan_sana' ga o'zgartirildi ###
    notifications = Bildirishnoma.objects.filter(user=request.user).order_by('-yaratilgan_sana')
    
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
        'active_page': 'bildirishnomalar',
    }
    return render(request, 'tests/notification_list.html', context)