# tests/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import TestSchedule, Question, AnswerOption

class TestScheduleForm(forms.ModelForm):
    # Vaqtni 24-soatlik, qo'lda yozsa bo'ladigan formatga keltiramiz
    open_time = forms.DateTimeField(
        label="Ochilish vaqti",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    close_time = forms.DateTimeField(
        label="Yopilish vaqti",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = TestSchedule
        fields = ['title', 'group', 'num_questions', 'is_active', 'open_time', 'close_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'num_questions': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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