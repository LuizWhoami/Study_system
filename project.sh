#!/bin/bash
# setup_project.sh - versão corrigida para ser executada DENTRO da pasta raiz do projeto

set -e

# Verifica se o diretório atual contém a estrutura esperada (apps/, templates/, etc.)
if [ ! -d "apps" ] || [ ! -d "templates" ]; then
    echo "⚠️  Parece que você não está na raiz do projeto (faltam pastas apps/ ou templates/)."
    echo "   Execute este script dentro da pasta que contém manage.py e apps/."
    exit 1
fi

echo "🚀 Criando arquivos do projeto em $(pwd)"

# -------------------------------
# 1. Arquivos do projeto principal (study_system/)
# -------------------------------

# Cria a subpasta do projeto se não existir (ela deve existir, mas garantimos)
mkdir -p study_system

# study_system/__init__.py
touch study_system/__init__.py

# study_system/settings.py
cat > study_system/settings.py << 'EOF'
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-0tq#e0q!0k-)n@9u4$&5&8+2$u6!c^u^u^x&c9d9^d9d9^d9d')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.core',
    'apps.contests',
    'apps.subjects',
    'apps.notes',
    'apps.study',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'study_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'study_system.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='study_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'

TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EOF

# study_system/urls.py
cat > study_system/urls.py << 'EOF'
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls')),
    path('concursos/', include('apps.contests.urls')),
    path('materias/', include('apps.subjects.urls')),
    path('notas/', include('apps.notes.urls')),
    path('estudo/', include('apps.study.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
EOF

# study_system/wsgi.py e asgi.py
cat > study_system/wsgi.py << 'EOF'
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_system.settings')
application = get_wsgi_application()
EOF

cat > study_system/asgi.py << 'EOF'
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_system.settings')
application = get_asgi_application()
EOF

# manage.py
cat > manage.py << 'EOF'
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_system.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
EOF
chmod +x manage.py

# ------------------------------------
# 2. Apps (accounts, contests, subjects, notes, study, dashboard)
# ------------------------------------
# Todos os arquivos de cada app serão criados dentro de apps/<app>/

# Função para criar os arquivos de um app
create_app_files() {
    local app=$1
    local dir="apps/$app"
    mkdir -p "$dir/migrations"
    touch "$dir/__init__.py"
    touch "$dir/migrations/__init__.py"

    # Cria models.py, admin.py, forms.py, views.py, urls.py apenas se não existirem
    # (para evitar sobrescrever se já houver conteúdo)
    [ ! -f "$dir/models.py" ] && touch "$dir/models.py"
    [ ! -f "$dir/admin.py" ] && touch "$dir/admin.py"
    [ ! -f "$dir/forms.py" ] && touch "$dir/forms.py"
    [ ! -f "$dir/views.py" ] && touch "$dir/views.py"
    [ ! -f "$dir/urls.py" ] && touch "$dir/urls.py"
}

# Criar estrutura para todos os apps
for app in accounts contests subjects notes study dashboard core; do
    create_app_files "$app"
done

# Agora preenchemos cada app com seu conteúdo (usando cat)

# ---------- accounts ----------
cat > apps/accounts/models.py << 'EOF'
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    photo = models.ImageField(upload_to='users/%Y/%m/', blank=True, null=True)
    main_goal = models.CharField(max_length=255, blank=True)
    daily_goal_hours = models.DecimalField(max_digits=5, decimal_places=2, default=3.0)
    preferred_study_time = models.TimeField(blank=True, null=True)
    available_days = models.JSONField(default=list)
    available_hours_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=4.0)

    def __str__(self):
        return self.username
EOF

cat > apps/accounts/admin.py << 'EOF'
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
admin.site.register(User, UserAdmin)
EOF

cat > apps/accounts/forms.py << 'EOF'
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
EOF

cat > apps/accounts/views.py << 'EOF'
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'accounts:login'

class CustomSignupView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
EOF

cat > apps/accounts/urls.py << 'EOF'
from django.urls import path
from . import views
app_name = 'accounts'
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.CustomSignupView.as_view(), name='signup'),
]
EOF

# ---------- contests ----------
cat > apps/contests/models.py << 'EOF'
from django.db import models
from django.conf import settings

class Contest(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planejando'),
        ('studying', 'Estudando'),
        ('review', 'Revisão'),
        ('intensive', 'Intensivo'),
        ('finished', 'Finalizado'),
        ('archived', 'Arquivado'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contests')
    name = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=200, blank=True)
    exam_date = models.DateField(blank=True, null=True)
    expected_date = models.DateField(blank=True, null=True)
    board = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    notes = models.TextField(blank=True)
    goal_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    goal_questions = models.IntegerField(default=0)
    priority = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'exam_date']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name
EOF

cat > apps/contests/admin.py << 'EOF'
from django.contrib import admin
from .models import Contest
@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'exam_date']
    list_filter = ['status', 'user']
    search_fields = ['name', 'organization']
EOF

cat > apps/contests/forms.py << 'EOF'
from django import forms
from .models import Contest

class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'organization', 'position', 'exam_date', 'expected_date',
                  'board', 'status', 'notes', 'goal_hours', 'goal_questions', 'priority']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_date': forms.DateInput(attrs={'type': 'date'}),
        }
EOF

cat > apps/contests/views.py << 'EOF'
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Contest
from .forms import ContestForm

class ContestListView(LoginRequiredMixin, ListView):
    model = Contest
    template_name = 'contests/list.html'
    context_object_name = 'contests'
    def get_queryset(self):
        return Contest.objects.filter(user=self.request.user)

class ContestCreateView(LoginRequiredMixin, CreateView):
    model = Contest
    form_class = ContestForm
    template_name = 'contests/form.html'
    success_url = reverse_lazy('contests:list')
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ContestUpdateView(LoginRequiredMixin, UpdateView):
    model = Contest
    form_class = ContestForm
    template_name = 'contests/form.html'
    success_url = reverse_lazy('contests:list')
    def get_queryset(self):
        return Contest.objects.filter(user=self.request.user)

class ContestDeleteView(LoginRequiredMixin, DeleteView):
    model = Contest
    template_name = 'contests/confirm_delete.html'
    success_url = reverse_lazy('contests:list')
    def get_queryset(self):
        return Contest.objects.filter(user=self.request.user)

class ContestDetailView(LoginRequiredMixin, DetailView):
    model = Contest
    template_name = 'contests/detail.html'
    context_object_name = 'contest'
    def get_queryset(self):
        return Contest.objects.filter(user=self.request.user)
EOF

cat > apps/contests/urls.py << 'EOF'
from django.urls import path
from . import views
app_name = 'contests'
urlpatterns = [
    path('', views.ContestListView.as_view(), name='list'),
    path('criar/', views.ContestCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.ContestUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.ContestDeleteView.as_view(), name='delete'),
    path('<int:pk>/', views.ContestDetailView.as_view(), name='detail'),
]
EOF

# ---------- subjects ----------
cat > apps/subjects/models.py << 'EOF'
from django.db import models
from django.conf import settings
from apps.contests.models import Contest

class Subject(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['contest', 'name']

    def __str__(self):
        return self.name

class Topic(models.Model):
    STATUS_CHOICES = [
        ('not_started', '⚪ Não iniciado'),
        ('studying', '🔵 Estudando'),
        ('studied', '🟡 Estudado'),
        ('review_pending', '🟠 Revisão pendente'),
        ('needs_reinforcement', '🔴 Precisa reforço'),
        ('mastered', '🟢 Dominado'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority = models.PositiveSmallIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)
    tags = models.ManyToManyField('notes.Tag', blank=True, related_name='topics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['subject', 'parent', 'name']

    def __str__(self):
        return self.name

    def get_full_path(self):
        names = [self.name]
        parent = self.parent
        while parent:
            names.append(parent.name)
            parent = parent.parent
        return ' → '.join(reversed(names))
EOF

cat > apps/subjects/admin.py << 'EOF'
from django.contrib import admin
from .models import Subject, Topic
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'contest', 'order']
    list_filter = ['contest']
    search_fields = ['name']
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'parent', 'status', 'priority']
    list_filter = ['status', 'subject']
    search_fields = ['name']
EOF

cat > apps/subjects/forms.py << 'EOF'
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
EOF

cat > apps/subjects/views.py << 'EOF'
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Subject
from .forms import SubjectForm

class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'subjects/list.html'
    context_object_name = 'subjects'
    def get_queryset(self):
        return Subject.objects.filter(contest__user=self.request.user)

class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/form.html'
    success_url = reverse_lazy('subjects:list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
EOF

cat > apps/subjects/urls.py << 'EOF'
from django.urls import path
from . import views
app_name = 'subjects'
urlpatterns = [
    path('', views.SubjectListView.as_view(), name='list'),
    path('criar/', views.SubjectCreateView.as_view(), name='create'),
]
EOF

# ---------- notes ----------
cat > apps/notes/models.py << 'EOF'
from django.db import models
from django.conf import settings
from apps.subjects.models import Topic

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')
    color = models.CharField(max_length=7, default='#6c757d')
    class Meta:
        unique_together = ['user', 'name']
    def __str__(self):
        return self.name

class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes')
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-updated_at']
    def __str__(self):
        return self.title
EOF

cat > apps/notes/admin.py << 'EOF'
from django.contrib import admin
from .models import Tag, Note
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color']
    list_filter = ['user']
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'topic', 'is_favorite', 'updated_at']
    list_filter = ['user', 'topic', 'is_favorite']
    search_fields = ['title', 'content']
EOF

cat > apps/notes/forms.py << 'EOF'
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
        self.fields['tags'].queryset = Tag.objects.filter(user=user)
EOF

cat > apps/notes/views.py << 'EOF'
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Note
from .forms import NoteForm

class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'notes/list.html'
    context_object_name = 'notes'
    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'notes/form.html'
    success_url = reverse_lazy('notes:list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'notes/form.html'
    success_url = reverse_lazy('notes:list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'notes/confirm_delete.html'
    success_url = reverse_lazy('notes:list')
    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

class NoteDetailView(LoginRequiredMixin, DetailView):
    model = Note
    template_name = 'notes/detail.html'
    context_object_name = 'note'
    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)
EOF

cat > apps/notes/urls.py << 'EOF'
from django.urls import path
from . import views
app_name = 'notes'
urlpatterns = [
    path('', views.NoteListView.as_view(), name='list'),
    path('criar/', views.NoteCreateView.as_view(), name='create'),
    path('<int:pk>/', views.NoteDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.NoteUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.NoteDeleteView.as_view(), name='delete'),
]
EOF

# ---------- study ----------
cat > apps/study/models.py << 'EOF'
from django.db import models
from django.conf import settings
from apps.subjects.models import Topic

class StudySession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class DailyProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_progress')
    date = models.DateField()
    hours_studied = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    questions_solved = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    flashcards_reviewed = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    class Meta:
        unique_together = ['user', 'date']
    def __str__(self):
        return f"{self.user.username} - {self.date}"

class Goal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    PERIOD_CHOICES = [('daily', 'Diária'), ('weekly', 'Semanal'), ('monthly', 'Mensal')]
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='daily')
    target_hours = models.DecimalField(max_digits=5, decimal_places=2, default=3.0)
    target_questions = models.PositiveIntegerField(default=30)
    target_flashcards = models.PositiveIntegerField(default=20)
    start_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.user.username} - {self.period}"
EOF

cat > apps/study/admin.py << 'EOF'
from django.contrib import admin
from .models import StudySession, DailyProgress, Goal
@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'start_time', 'duration_minutes']
    list_filter = ['user', 'topic']
@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'hours_studied', 'questions_solved']
    list_filter = ['user']
@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'target_hours', 'active']
    list_filter = ['user', 'period', 'active']
EOF

cat > apps/study/forms.py << 'EOF'
from django import forms
from .models import Goal
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['period', 'target_hours', 'target_questions', 'target_flashcards', 'active']
EOF

cat > apps/study/views.py << 'EOF'
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import StudySession, DailyProgress
from apps.subjects.models import Topic

@login_required
def timer_view(request):
    topics = Topic.objects.filter(subject__contest__user=request.user)
    return render(request, 'study/timer.html', {'topics': topics})

@login_required
def start_session(request):
    if request.method == 'POST':
        topic_id = request.POST.get('topic')
        topic = get_object_or_404(Topic, id=topic_id, subject__contest__user=request.user)
        session = StudySession.objects.create(
            user=request.user,
            topic=topic,
            start_time=timezone.now()
        )
        return JsonResponse({'session_id': session.id})
    return JsonResponse({'error': 'Método inválido'}, status=400)

@login_required
def end_session(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        duration_minutes = request.POST.get('duration_minutes')
        session = get_object_or_404(StudySession, id=session_id, user=request.user)
        session.end_time = timezone.now()
        session.duration_minutes = int(duration_minutes)
        session.save()
        today = timezone.now().date()
        progress, created = DailyProgress.objects.get_or_create(user=request.user, date=today)
        progress.hours_studied += int(duration_minutes) / 60
        progress.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Método inválido'}, status=400)
EOF

cat > apps/study/urls.py << 'EOF'
from django.urls import path
from . import views
app_name = 'study'
urlpatterns = [
    path('timer/', views.timer_view, name='timer'),
    path('start/', views.start_session, name='start_session'),
    path('end/', views.end_session, name='end_session'),
]
EOF

# ---------- dashboard ----------
cat > apps/dashboard/views.py << 'EOF'
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from apps.study.models import StudySession, DailyProgress
from apps.subjects.models import Topic

@login_required
def index(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    sessions_today = StudySession.objects.filter(user=user, start_time__date=today)
    hours_today = (sessions_today.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60

    sessions_week = StudySession.objects.filter(user=user, start_time__date__gte=week_ago)
    hours_week = (sessions_week.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60

    sessions_month = StudySession.objects.filter(user=user, start_time__date__gte=month_ago)
    hours_month = (sessions_month.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60

    progress_today = DailyProgress.objects.filter(user=user, date=today).first()
    questions_today = progress_today.questions_solved if progress_today else 0
    correct_today = progress_today.correct_answers if progress_today else 0
    accuracy = (correct_today / questions_today * 100) if questions_today > 0 else 0

    reviews_pending = Topic.objects.filter(subject__contest__user=user, status='review_pending').count()

    streak = 0
    current_date = today
    while True:
        daily = DailyProgress.objects.filter(user=user, date=current_date).first()
        if daily and daily.hours_studied > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    total_topics = Topic.objects.filter(subject__contest__user=user).count()
    mastered = Topic.objects.filter(subject__contest__user=user, status='mastered').count()
    progress_general = (mastered / total_topics * 100) if total_topics > 0 else 0

    last_sessions = StudySession.objects.filter(user=user).order_by('-start_time')[:5]

    context = {
        'hours_today': round(hours_today, 2),
        'hours_week': round(hours_week, 2),
        'hours_month': round(hours_month, 2),
        'questions_today': questions_today,
        'accuracy': round(accuracy, 2),
        'reviews_pending': reviews_pending,
        'streak': streak,
        'progress_general': round(progress_general, 2),
        'last_sessions': last_sessions,
        'daily_goal_hours': user.daily_goal_hours,
    }
    return render(request, 'dashboard/index.html', context)
EOF

cat > apps/dashboard/urls.py << 'EOF'
from django.urls import path
from . import views
app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
]
EOF

# ---------- core (vazio) ----------
touch apps/core/__init__.py
touch apps/core/models.py
touch apps/core/views.py
touch apps/core/admin.py

# ------------------------------------
# 3. Templates
# ------------------------------------
# base.html
cat > templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Study System{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/style.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  <div class="d-flex" id="wrapper">
    <div class="bg-dark text-white" id="sidebar-wrapper" style="min-width: 250px; min-height: 100vh;">
      <div class="sidebar-heading text-center py-4 primary-text fs-4 fw-bold text-uppercase border-bottom">StudySystem</div>
      <div class="list-group list-group-flush my-3">
        <a href="{% url 'dashboard:index' %}" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-speedometer2 me-2"></i>Dashboard</a>
        <a href="{% url 'contests:list' %}" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-briefcase me-2"></i>Concursos</a>
        <a href="{% url 'subjects:list' %}" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-book me-2"></i>Matérias</a>
        <a href="{% url 'notes:list' %}" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-sticky me-2"></i>Notas</a>
        <a href="{% url 'study:timer' %}" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-clock me-2"></i>Cronômetro</a>
        <a href="#" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-card-checklist me-2"></i>Flashcards</a>
        <a href="#" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-question-circle me-2"></i>Questões</a>
        <a href="#" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-calendar me-2"></i>Calendário</a>
        <a href="#" class="list-group-item list-group-item-action bg-transparent text-white"><i class="bi bi-bar-chart me-2"></i>Estatísticas</a>
      </div>
    </div>
    <div id="page-content-wrapper" class="w-100">
      <nav class="navbar navbar-expand-lg navbar-light bg-light border-bottom">
        <div class="container-fluid">
          <button class="btn btn-primary" id="menu-toggle"><i class="bi bi-list"></i></button>
          <div class="ms-auto">
            <span class="me-3">Olá, {{ user.username }}</span>
            <a href="{% url 'accounts:logout' %}" class="btn btn-outline-danger btn-sm">Sair</a>
          </div>
        </div>
      </nav>
      <div class="container-fluid px-4 py-4">
        {% block content %}{% endblock %}
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    document.getElementById("menu-toggle").addEventListener("click", function(e) {
      e.preventDefault();
      document.getElementById("wrapper").classList.toggle("toggled");
    });
  </script>
  {% block extra_js %}{% endblock %}
</body>
</html>
EOF

# dashboard/index.html
mkdir -p templates/dashboard
cat > templates/dashboard/index.html << 'EOF'
{% extends 'base.html' %}
{% load static %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<div class="row">
  <div class="col-md-3 col-sm-6 mb-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Horas hoje</h5>
        <p class="display-6">{{ hours_today }}h</p>
        <small>Meta: {{ daily_goal_hours }}h</small>
      </div>
    </div>
  </div>
  <div class="col-md-3 col-sm-6 mb-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Horas semana</h5>
        <p class="display-6">{{ hours_week }}h</p>
      </div>
    </div>
  </div>
  <div class="col-md-3 col-sm-6 mb-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Horas mês</h5>
        <p class="display-6">{{ hours_month }}h</p>
      </div>
    </div>
  </div>
  <div class="col-md-3 col-sm-6 mb-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Questões hoje</h5>
        <p class="display-6">{{ questions_today }}</p>
        <small>Acertos: {{ accuracy }}%</small>
      </div>
    </div>
  </div>
</div>
<div class="row">
  <div class="col-md-6">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Progresso geral</h5>
        <div class="progress">
          <div class="progress-bar" role="progressbar" style="width: {{ progress_general }}%;" aria-valuenow="{{ progress_general }}" aria-valuemin="0" aria-valuemax="100">{{ progress_general }}%</div>
        </div>
        <p class="mt-2">Streak: 🔥 {{ streak }} dias</p>
        <p>Revisões pendentes: {{ reviews_pending }}</p>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Últimas sessões</h5>
        <ul class="list-group">
          {% for session in last_sessions %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
              {{ session.topic.name|default:"Sem tópico" }}
              <span>{{ session.duration_minutes }} min</span>
            </li>
          {% empty %}
            <li class="list-group-item">Nenhuma sessão registrada.</li>
          {% endfor %}
        </ul>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

# accounts templates
mkdir -p templates/accounts
cat > templates/accounts/login.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header">Login</div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          {{ form.as_p }}
          <button type="submit" class="btn btn-primary">Entrar</button>
          <a href="{% url 'accounts:signup' %}" class="btn btn-link">Criar conta</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

cat > templates/accounts/signup.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header">Cadastro</div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          {{ form.as_p }}
          <button type="submit" class="btn btn-primary">Cadastrar</button>
          <a href="{% url 'accounts:login' %}" class="btn btn-link">Já tenho conta</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

# contests templates
mkdir -p templates/contests
cat > templates/contests/list.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h2>Meus Concursos</h2>
  <a href="{% url 'contests:create' %}" class="btn btn-primary">Novo Concurso</a>
</div>
<div class="row">
  {% for contest in contests %}
    <div class="col-md-4 mb-3">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">{{ contest.name }}</h5>
          <p class="card-text">{{ contest.organization }} - {{ contest.position }}</p>
          <p>Status: {{ contest.get_status_display }}</p>
          <p>Prova: {{ contest.exam_date|default:"Não definida" }}</p>
          <a href="{% url 'contests:detail' contest.pk %}" class="btn btn-sm btn-outline-primary">Ver</a>
          <a href="{% url 'contests:update' contest.pk %}" class="btn btn-sm btn-outline-secondary">Editar</a>
          <a href="{% url 'contests:delete' contest.pk %}" class="btn btn-sm btn-outline-danger">Excluir</a>
        </div>
      </div>
    </div>
  {% empty %}
    <p>Nenhum concurso cadastrado.</p>
  {% endfor %}
</div>
{% endblock %}
EOF

cat > templates/contests/form.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-8">
    <div class="card">
      <div class="card-header">{{ view.action|default:"Formulário" }}</div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          {{ form.as_p }}
          <button type="submit" class="btn btn-success">Salvar</button>
          <a href="{% url 'contests:list' %}" class="btn btn-secondary">Cancelar</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

cat > templates/contests/detail.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<h2>{{ contest.name }}</h2>
<p><strong>Orgão:</strong> {{ contest.organization }}</p>
<p><strong>Cargo:</strong> {{ contest.position }}</p>
<p><strong>Data da prova:</strong> {{ contest.exam_date|default:"Não definida" }}</p>
<p><strong>Banca:</strong> {{ contest.board }}</p>
<p><strong>Status:</strong> {{ contest.get_status_display }}</p>
<p><strong>Observações:</strong> {{ contest.notes|linebreaks }}</p>
<a href="{% url 'contests:update' contest.pk %}" class="btn btn-warning">Editar</a>
<a href="{% url 'contests:list' %}" class="btn btn-secondary">Voltar</a>
{% endblock %}
EOF

cat > templates/contests/confirm_delete.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header">Confirmar exclusão</div>
      <div class="card-body">
        <p>Tem certeza que deseja excluir o concurso "{{ object.name }}"?</p>
        <form method="post">
          {% csrf_token %}
          <button type="submit" class="btn btn-danger">Sim, excluir</button>
          <a href="{% url 'contests:list' %}" class="btn btn-secondary">Cancelar</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

# subjects templates
mkdir -p templates/subjects
cat > templates/subjects/list.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<h2>Matérias</h2>
<a href="{% url 'subjects:create' %}" class="btn btn-primary mb-3">Nova Matéria</a>
<ul class="list-group">
  {% for subject in subjects %}
    <li class="list-group-item">{{ subject.name }} ({{ subject.contest.name }})</li>
  {% empty %}
    <li class="list-group-item">Nenhuma matéria cadastrada.</li>
  {% endfor %}
</ul>
{% endblock %}
EOF

cat > templates/subjects/form.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header">Nova Matéria</div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          {{ form.as_p }}
          <button type="submit" class="btn btn-success">Salvar</button>
          <a href="{% url 'subjects:list' %}" class="btn btn-secondary">Cancelar</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

# notes templates
mkdir -p templates/notes
cat > templates/notes/list.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h2>Minhas Notas</h2>
  <a href="{% url 'notes:create' %}" class="btn btn-primary">Nova Nota</a>
</div>
<div class="row">
  {% for note in notes %}
    <div class="col-md-4 mb-3">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">{{ note.title }}</h5>
          <p class="card-text">{{ note.content|truncatewords:20 }}</p>
          <p><small>Tópico: {{ note.topic.name }}</small></p>
          <a href="{% url 'notes:detail' note.pk %}" class="btn btn-sm btn-outline-primary">Ver</a>
          <a href="{% url 'notes:update' note.pk %}" class="btn btn-sm btn-outline-secondary">Editar</a>
          <a href="{% url 'notes:delete' note.pk %}" class="btn btn-sm btn-outline-danger">Excluir</a>
        </div>
      </div>
    </div>
  {% empty %}
    <p>Nenhuma nota criada.</p>
  {% endfor %}
</div>
{% endblock %}
EOF

cat > templates/notes/form.html << 'EOF'
{% extends 'base.html' %}
{% load static %}
{% block extra_css %}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/easymde/dist/easymde.min.css">
{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-8">
    <div class="card">
      <div class="card-header">Nova Nota</div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          {{ form.as_p }}
          <button type="submit" class="btn btn-success">Salvar</button>
          <a href="{% url 'notes:list' %}" class="btn btn-secondary">Cancelar</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/easymde/dist/easymde.min.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    var textareas = document.querySelectorAll('.markdown-editor');
    textareas.forEach(function(ta) {
      new EasyMDE({ element: ta });
    });
  });
</script>
{% endblock %}
EOF

cat > templates/notes/detail.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<h2>{{ note.title }}</h2>
<p><strong>Tópico:</strong> {{ note.topic.name }}</p>
<div class="border p-3">
  {{ note.content|linebreaks }}
</div>
<p><strong>Tags:</strong> 
  {% for tag in note.tags.all %}
    <span class="badge bg-secondary">{{ tag.name }}</span>
  {% endfor %}
</p>
<a href="{% url 'notes:update' note.pk %}" class="btn btn-warning">Editar</a>
<a href="{% url 'notes:list' %}" class="btn btn-secondary">Voltar</a>
{% endblock %}
EOF

cat > templates/notes/confirm_delete.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header">Confirmar exclusão</div>
      <div class="card-body">
        <p>Tem certeza que deseja excluir a nota "{{ object.title }}"?</p>
        <form method="post">
          {% csrf_token %}
          <button type="submit" class="btn btn-danger">Sim, excluir</button>
          <a href="{% url 'notes:list' %}" class="btn btn-secondary">Cancelar</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

# study timer
mkdir -p templates/study
cat > templates/study/timer.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<h2>Cronômetro de Estudo</h2>
<div class="row">
  <div class="col-md-6">
    <div class="card">
      <div class="card-body">
        <form id="timer-form">
          <div class="mb-3">
            <label for="topic" class="form-label">Tópico</label>
            <select class="form-select" id="topic" name="topic" required>
              <option value="">Selecione...</option>
              {% for topic in topics %}
                <option value="{{ topic.id }}">{{ topic.get_full_path }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="mb-3">
            <label class="form-label">Duração</label>
            <div id="timer-display" class="display-4">00:00:00</div>
          </div>
          <div class="btn-group">
            <button type="button" class="btn btn-success" id="start-btn">Iniciar</button>
            <button type="button" class="btn btn-warning" id="pause-btn" disabled>Pausar</button>
            <button type="button" class="btn btn-danger" id="end-btn" disabled>Finalizar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
<script>
  let timerInterval = null;
  let seconds = 0;
  let sessionId = null;
  let isRunning = false;

  const display = document.getElementById('timer-display');
  const startBtn = document.getElementById('start-btn');
  const pauseBtn = document.getElementById('pause-btn');
  const endBtn = document.getElementById('end-btn');

  function formatTime(s) {
    const h = String(Math.floor(s / 3600)).padStart(2, '0');
    const m = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
    const sec = String(s % 60).padStart(2, '0');
    return `${h}:${m}:${sec}`;
  }

  function updateDisplay() {
    display.textContent = formatTime(seconds);
  }

  function startTimer() {
    const topicId = document.getElementById('topic').value;
    if (!topicId) {
      alert('Selecione um tópico.');
      return;
    }
    fetch("{% url 'study:start_session' %}", {
      method: 'POST',
      headers: { 'X-CSRFToken': '{{ csrf_token }}' },
      body: new URLSearchParams({ topic: topicId })
    })
    .then(response => response.json())
    .then(data => {
      sessionId = data.session_id;
      if (timerInterval) clearInterval(timerInterval);
      seconds = 0;
      updateDisplay();
      timerInterval = setInterval(() => {
        seconds++;
        updateDisplay();
      }, 1000);
      isRunning = true;
      startBtn.disabled = true;
      pauseBtn.disabled = false;
      endBtn.disabled = false;
    });
  }

  function pauseTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
      isRunning = false;
      pauseBtn.textContent = 'Continuar';
    } else {
      timerInterval = setInterval(() => {
        seconds++;
        updateDisplay();
      }, 1000);
      isRunning = true;
      pauseBtn.textContent = 'Pausar';
    }
  }

  function endTimer() {
    if (timerInterval) clearInterval(timerInterval);
    if (sessionId) {
      fetch("{% url 'study:end_session' %}", {
        method: 'POST',
        headers: { 'X-CSRFToken': '{{ csrf_token }}' },
        body: new URLSearchParams({ session_id: sessionId, duration_minutes: Math.floor(seconds / 60) })
      })
      .then(response => response.json())
      .then(data => {
        alert('Sessão finalizada!');
        resetTimer();
      });
    } else {
      resetTimer();
    }
  }

  function resetTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    seconds = 0;
    updateDisplay();
    isRunning = false;
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    endBtn.disabled = true;
    pauseBtn.textContent = 'Pausar';
    sessionId = null;
  }

  startBtn.addEventListener('click', startTimer);
  pauseBtn.addEventListener('click', pauseTimer);
  endBtn.addEventListener('click', endTimer);
</script>
{% endblock %}
EOF

# ------------------------------------
# 4. CSS
# ------------------------------------
cat > static/css/style.css << 'EOF'
body {
  background-color: #f8f9fa;
}
#sidebar-wrapper {
  min-height: 100vh;
  margin-left: -250px;
  transition: margin 0.25s ease-out;
}
#wrapper.toggled #sidebar-wrapper {
  margin-left: 0;
}
#page-content-wrapper {
  min-width: 100vw;
}
#wrapper.toggled #page-content-wrapper {
  min-width: 0;
  width: 100%;
}
@media (min-width: 768px) {
  #sidebar-wrapper {
    margin-left: 0;
  }
  #page-content-wrapper {
    min-width: 0;
    width: 100%;
  }
  #wrapper.toggled #sidebar-wrapper {
    margin-left: -250px;
  }
}
EOF

# ------------------------------------
# 5. Finalização
# ------------------------------------
echo "✅ Todos os arquivos foram criados com sucesso!"
echo ""
echo "Agora execute:"
echo "  python manage.py makemigrations"
echo "  python manage.py migrate"
echo "  python manage.py createsuperuser"
echo "  python manage.py runserver"
