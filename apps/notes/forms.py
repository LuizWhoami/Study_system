from django import forms
from .models import Note, Tag
from apps.subjects.models import Topic

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['topic', 'title', 'content', 'tags', 'is_favorite']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'markdown-editor'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['topic'].queryset = Topic.objects.filter(subject__contest__user=user)
        self.fields['topic'].required = False  # <--- Torna opcional
        self.fields['tags'].queryset = Tag.objects.filter(user=user)
