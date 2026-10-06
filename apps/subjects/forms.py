from django import forms
from .models import Subject, Topic
from apps.contests.models import Contest


class SubjectForm(forms.ModelForm):
    """Formulário de criação/edição de matéria."""

    class Meta:
        model = Subject
        fields = ['contest', 'name']  # 'order' saiu — é técnico
        widgets = {
            'contest': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Direito Constitucional',
                'autofocus': True,
            }),
        }
        labels = {
            'contest': 'Concurso',
            'name': 'Nome da matéria',
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contest'].queryset = Contest.objects.filter(
            user=user
        ).order_by('name')

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Informe o nome da matéria.')
        return name


class TopicForm(forms.ModelForm):
    """Formulário de criação/edição de tópico."""

    class Meta:
        model = Topic
        fields = ['subject', 'parent', 'name', 'status', 'priority', 'tags']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Princípios fundamentais',
                'autofocus': True,
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5,
            }),
        }
        labels = {
            'subject': 'Matéria',
            'parent': 'Tópico pai',
            'name': 'Nome do tópico',
            'status': 'Status',
            'priority': 'Prioridade',
            'tags': 'Tags',
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(
            contest__user=user
        ).select_related('contest').order_by('contest__name', 'name')

        self.fields['parent'].queryset = Topic.objects.filter(
            subject__contest__user=user
        ).select_related('subject').order_by('subject__name', 'name')

        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "Nenhum (tópico raiz)"
