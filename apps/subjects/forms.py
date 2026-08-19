from django import forms
from .models import Subject, Topic
from apps.contests.models import Contest

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['contest', 'name', 'order']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contest'].queryset = Contest.objects.filter(user=user)

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['subject', 'parent', 'name', 'status', 'priority', 'order', 'tags']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(contest__user=user)
        self.fields['parent'].queryset = Topic.objects.filter(subject__contest__user=user)
