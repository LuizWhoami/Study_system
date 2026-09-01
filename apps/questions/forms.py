from django import forms
from .models import Question
from apps.subjects.models import Topic
from apps.contests.models import Contest

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'contest', 'topic', 'enunciado',
            'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d',
            'alternativa_correta', 'explicacao', 'dificuldade',
            'banca', 'ano', 'fonte', 'status'
        ]
        widgets = {
            'enunciado': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'explicacao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'alternativa_a': forms.TextInput(attrs={'class': 'form-control'}),
            'alternativa_b': forms.TextInput(attrs={'class': 'form-control'}),
            'alternativa_c': forms.TextInput(attrs={'class': 'form-control'}),
            'alternativa_d': forms.TextInput(attrs={'class': 'form-control'}),
            'alternativa_correta': forms.Select(attrs={'class': 'form-select'}),
            'dificuldade': forms.Select(attrs={'class': 'form-select'}),
            'banca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CESPE, FCC, Vunesp'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2024'}),
            'fonte': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Prova X, Livro Y'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contest': forms.Select(attrs={'class': 'form-select'}),
            'topic': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'contest': 'Concurso/Estudo',
            'topic': 'Assunto',
            'enunciado': 'Enunciado',
            'alternativa_a': 'Alternativa A',
            'alternativa_b': 'Alternativa B',
            'alternativa_c': 'Alternativa C',
            'alternativa_d': 'Alternativa D',
            'alternativa_correta': 'Resposta correta',
            'explicacao': 'Explicação',
            'dificuldade': 'Dificuldade',
            'banca': 'Banca',
            'ano': 'Ano',
            'fonte': 'Fonte',
            'status': 'Ativa',
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contest'].queryset = Contest.objects.filter(user=user)
        self.fields['topic'].queryset = Topic.objects.filter(
            subject__contest__user=user
        ).select_related('subject__contest')
        self.fields['contest'].empty_label = 'Nenhum'
        self.fields['topic'].empty_label = 'Selecione...'
        self.fields['ano'].required = False
        self.fields['banca'].required = False
        self.fields['fonte'].required = False
