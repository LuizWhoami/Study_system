from django import forms
from .models import Contest


class ContestForm(forms.ModelForm):
    """
    Formulário de criação/edição de concurso.

    Os widgets já trazem as classes do design system (`form-control`,
    `form-select`), então o template não precisa de CSS defensivo.
    """

    PRIORITY_CHOICES = [
        (0, 'Nenhuma'),
        (1, 'Baixa'),
        (2, 'Média'),
        (3, 'Alta'),
        (4, 'Urgente'),
    ]

    # Sobrescrevemos `priority` para virar select legível em vez de número cru.
    # O model continua `PositiveSmallIntegerField` — sem migration.
    priority = forms.TypedChoiceField(
        choices=PRIORITY_CHOICES,
        coerce=int,
        initial=0,
        required=False,
        label='Prioridade',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Contest
        fields = [
            'name', 'organization', 'position', 'main_topic',
            'exam_date', 'expected_date', 'board', 'status',
            'notes', 'goal_hours', 'goal_questions', 'priority',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: PF Agente 2026',
                'autofocus': True,
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Polícia Federal',
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Agente de Polícia',
            }),
            'main_topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Direito Constitucional',
            }),
            'exam_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'expected_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'board': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CEBRASPE',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observações livres sobre este concurso...',
            }),
            'goal_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': '0.5',
                'placeholder': '0',
            }),
            'goal_questions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '0',
            }),
        }
        labels = {
            'name': 'Nome',
            'organization': 'Órgão / Instituição',
            'position': 'Cargo / Objetivo',
            'main_topic': 'Tópico principal',
            'exam_date': 'Data da prova',
            'expected_date': 'Data prevista',
            'board': 'Banca',
            'status': 'Status',
            'notes': 'Observações',
            'goal_hours': 'Meta de horas',
            'goal_questions': 'Meta de questões',
        }
        help_texts = {
            'main_topic': 'Ex: "Direito Constitucional", "Matemática"',
        }

    def clean_name(self):
        """Garante que o nome não é só espaços em branco."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Informe um nome.')
        return name

    def clean_goal_hours(self):
        value = self.cleaned_data.get('goal_hours') or 0
        if value < 0:
            raise forms.ValidationError('A meta de horas não pode ser negativa.')
        return value

    def clean_goal_questions(self):
        value = self.cleaned_data.get('goal_questions') or 0
        if value < 0:
            raise forms.ValidationError('A meta de questões não pode ser negativa.')
        return value
