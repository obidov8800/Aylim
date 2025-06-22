# tests/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import TestSchedule, Question, AnswerOption

class TestScheduleForm(forms.ModelForm):
    class Meta:
        model = TestSchedule
        fields = ['title', 'group', 'open_time', 'close_time', 'num_questions', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'num_questions': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Talabaga beriladigan savollar soni'}),
            'open_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'close_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BaseAnswerFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        
        correct_answers_count = 0
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_correct', False):
                    correct_answers_count += 1
        
        if self.forms and correct_answers_count == 0:
            raise forms.ValidationError('Har bir savol uchun kamida bitta to\'g\'ri javob belgilanishi shart.')
        if correct_answers_count > 1:
            raise forms.ValidationError('Faqat bitta javob to\'g\'ri deb belgilanishi mumkin.')

AnswerFormSet = inlineformset_factory(
    Question, AnswerOption, formset=BaseAnswerFormSet,
    fields=('answer_text', 'is_correct'), extra=4, max_num=4, can_delete=False,
    widgets={'answer_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Javob matni'}),}
)

class ImportQuestionsForm(forms.Form):
    file = forms.FileField(label="Savollar fayli (.docx)")