from django import forms
from .models import Goal
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['period', 'target_hours', 'target_questions', 'target_flashcards', 'active']
