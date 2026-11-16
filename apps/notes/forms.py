from django import forms
from .models import Note, Tag, NoteFolder
from apps.subjects.models import Topic


class NoteFolderForm(forms.ModelForm):
    class Meta:
        model = NoteFolder
        fields = ['name', 'color', 'description']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'description': forms.TextInput(attrs={'placeholder': 'Opcional'}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['folder', 'topic', 'title', 'content', 'tags', 'is_favorite']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'markdown-editor'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['topic'].queryset = Topic.objects.filter(subject__contest__user=user)
        self.fields['topic'].required = False
        self.fields['tags'].queryset = Tag.objects.filter(user=user)
        self.fields['folder'].queryset = NoteFolder.objects.filter(user=user)
        self.fields['folder'].required = False
