# tests/admin.py

from django.contrib import admin
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils import timezone
from .models import Group, TestSchedule, Question, AnswerOption, TestResult, Bildirishnoma, Fan, DarsJadvali, AttendanceRecord

# --- MAXSUS FILTR YARATAMIZ ---
class TestStatusFilter(admin.SimpleListFilter):
    title = 'Holati bo\'yicha' # Filtrning sarlavhasi
    parameter_name = 'status' # URL'dagi parametr nomi

    def lookups(self, request, model_admin):
        # Filtrning variantlari
        return (
            ('active', 'Aktiv'),
            ('upcoming', 'Yaqinlashayotgan'),
            ('finished', 'Tugagan'),
        )

    def queryset(self, request, queryset):
        # Tanlangan variantga qarab queryset'ni filtrlash
        now = timezone.now()
        if self.value() == 'active':
            return queryset.filter(open_time__lte=now, close_time__gte=now)
        if self.value() == 'upcoming':
            return queryset.filter(open_time__gt=now)
        if self.value() == 'finished':
            return queryset.filter(close_time__lt=now)
        return queryset

# AnswerOption modelini Question ostida inline qilish uchun
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4

# Question modelini TestSchedule ostida inline qilish uchun
class QuestionInline(admin.TabularInline):
    model = Question
    inlines = [AnswerOptionInline]
    extra = 1


@admin.register(TestSchedule)
class TestScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'open_time', 'close_time', 'num_questions', 'is_active', 'import_questions_link')
    # list_filter'dagi 'is_active' o'rniga yangi filtrni ishlatamiz
    list_filter = ('group', TestStatusFilter) # <-- O'ZGARTIRILDI
    search_fields = ('title', 'group__name')
    inlines = [QuestionInline]
    actions = ['duplicate_tests', 'export_results_pdf_action']

    def import_questions_link(self, obj):
        url = reverse('tests:import_questions', args=[obj.pk])
        return format_html('<a href="{}">Savol import</a>', url)
    import_questions_link.short_description = "Savol import qilish"

    # ... qolgan barcha metodlar (duplicate_tests, export_results_pdf_action) o'zgarishsiz qoladi
    # ...


# Qolgan admin klasslari o'zgarishsiz qoladi
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('test_schedule', 'question_text')
    list_filter = ('test_schedule',)
    search_fields = ('question_text',)
    inlines = [AnswerOptionInline]

# ... va hokazo boshqa admin registerlar ...
admin.site.register(AnswerOption)
admin.site.register(TestResult)
admin.site.register(Bildirishnoma)

@admin.register(Fan)
class FanAdmin(admin.ModelAdmin):
    list_display = ('nomi',)
    search_fields = ('nomi',)

@admin.register(DarsJadvali)
class DarsJadvaliAdmin(admin.ModelAdmin):
    list_display = ('hafta_kuni', 'boshlanish_vaqti', 'tugash_vaqti', 'fan', 'guruh', 'oqtuvchi', 'xona')
    list_filter = ('guruh', 'oqtuvchi', 'hafta_kuni', 'fan')
    search_fields = ('fan__nomi', 'guruh__name', 'oqtuvchi__full_name')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    
    def changelist_view(self, request, extra_context=None):
        """
        Admin panelda "Davomat Yozuvlari" bo'limiga bosilganda, 
        foydalanuvchini to'g'ridan-to'g'ri o'zimizning interaktiv 
        sahifamizga yo'naltiradi.
        """
        return redirect('tests:attendance_management')