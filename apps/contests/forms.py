from django import forms
from .models import Contest

class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'organization', 'position', 'start_date', 'exam_date', 'expected_date',
                  'board', 'status', 'notes', 'goal_hours', 'goal_questions', 'priority']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_date': forms.DateInput(attrs={'type': 'date'}),
        }
