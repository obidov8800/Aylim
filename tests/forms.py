# tests/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import TestSchedule, Question, AnswerOption, Group

class TestScheduleForm(forms.ModelForm):
    # Bu maydonlar modelda mavjud deb hisoblaymiz (oldingi model tahrirlariga asosan)
    test_date = forms.DateField(
        label="Test sanasi",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        label="Boshlanish vaqti",
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        label="Tugash vaqti",
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'})
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Guruh",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = TestSchedule
        # fields qismida modelingizdagi barcha tegishli maydonlar mavjudligiga ishonch hosil qiling
        fields = ['author', 'title', 'tavsif', 'group', 'num_questions', 'test_date', 'start_time', 'end_time', 'davomiyligi', 'is_active']

        widgets = {
            'author': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'tavsif': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'davomiyligi': forms.NumberInput(attrs={'class': 'form-control'}),
            'num_questions': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # test_date, start_time, end_time uchun widgetlar yuqorida aniqlangan, bu yerda takrorlash shart emas.
        }
        labels = {
            'author': "Muallif",
            'title': "Test sarlavhasi",
            'tavsif': "Tavsif",
            'davomiyligi': "Davomiyligi (daqiqa)",
            'num_questions': "Savollar soni",
            'is_active': "Aktiv",
            # test_date, start_time, end_time, group uchun labellar yuqorida aniqlangan.
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Savol matnini kiriting'}),
        }

class BaseAnswerFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        
        has_at_least_one_form = False
        correct_answers_count = 0
        for form in self.forms:
            if form.is_valid() and form.has_changed() and not form.cleaned_data.get('DELETE', False):
                has_at_least_one_form = True
                if form.cleaned_data.get('is_correct'):
                    correct_answers_count += 1
        
        if has_at_least_one_form and correct_answers_count != 1:
            raise forms.ValidationError("Har bir savol uchun aniq bitta to'g'ri javob belgilanishi shart.")

AnswerFormSet = inlineformset_factory(
    Question, AnswerOption,
    formset=BaseAnswerFormSet,
    fields=('answer_text', 'is_correct'),
    extra=4, max_num=4, can_delete=True,
    widgets={
        'answer_text': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Javob varianti'}),
        'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)

class ImportQuestionsForm(forms.Form):
    file = forms.FileField(label="Faylni tanlang", widget=forms.FileInput(attrs={'class': 'form-control'}))