#!/bin/bash
# update_general.sh – transforma "Concursos" em "Estudos" e adiciona mapa geral

set -e

echo "🔄 Atualizando sistema para Estudos Gerais..."

# 1. Atualizar modelo Contest: adicionar start_date, mudar verbose_name
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contests', verbose_name="Usuário")
    name = models.CharField(max_length=200, verbose_name="Nome do Estudo")
    organization = models.CharField(max_length=200, blank=True, verbose_name="Instituição/Curso")
    position = models.CharField(max_length=200, blank=True, verbose_name="Objetivo")
    start_date = models.DateField(blank=True, null=True, verbose_name="Data de Início")
    exam_date = models.DateField(blank=True, null=True, verbose_name="Data da Prova/Meta")
    expected_date = models.DateField(blank=True, null=True, verbose_name="Data Prevista (opcional)")
    board = models.CharField(max_length=100, blank=True, verbose_name="Banca/Instituição")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name="Status")
    notes = models.TextField(blank=True, verbose_name="Observações")
    goal_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Meta de Horas")
    goal_questions = models.IntegerField(default=0, verbose_name="Meta de Questões")
    priority = models.PositiveSmallIntegerField(default=0, verbose_name="Prioridade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['-priority', 'exam_date']
        unique_together = ['user', 'name']
        verbose_name = "Estudo"
        verbose_name_plural = "Estudos"

    def __str__(self):
        return self.name

    def get_progress(self):
        # Calcula progresso baseado em tópicos concluídos (status 'mastered' ou 'studied')
        total_topics = self.subjects.aggregate(total=models.Count('topics'))['total'] or 0
        if total_topics == 0:
            return 0
        mastered = self.subjects.aggregate(
            mastered=models.Count('topics', filter=models.Q(topics__status='mastered'))
        )['mastered'] or 0
        return int((mastered / total_topics) * 100)
EOF

# 2. Atualizar formulário para incluir start_date
cat > apps/contests/forms.py << 'EOF'
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
EOF

# 3. Atualizar views: adicionar general_view
cat > apps/contests/views.py << 'EOF'
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render
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

# Nova view: página geral com mapa
class GeneralView(LoginRequiredMixin, TemplateView):
    template_name = 'contests/general.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        estudos = Contest.objects.filter(user=user)
        dados_estudos = []
        for estudo in estudos:
            progresso = estudo.get_progress()
            dados_estudos.append({
                'estudo': estudo,
                'progresso': progresso,
                'total_topics': estudo.subjects.aggregate(total=models.Count('topics'))['total'] or 0,
            })
        context['estudos'] = dados_estudos
        return context
EOF

# 4. Atualizar urls: adicionar rota para general
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
    path('geral/', views.GeneralView.as_view(), name='general'),
]
EOF

# 5. Criar template da página geral com mapa
cat > templates/contests/general.html << 'EOF'
{% extends 'base.html' %}
{% load static %}
{% block title %}Visão Geral dos Estudos{% endblock %}

{% block content %}
<h2 class="mb-4"><i class="bi bi-globe2 me-2"></i>Visão Geral dos Estudos</h2>

{% if estudos %}
  <div class="row g-4">
    {% for item in estudos %}
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <h5 class="card-title">{{ item.estudo.name }}</h5>
              <span class="badge bg-{% if item.estudo.status == 'studying' %}primary{% elif item.estudo.status == 'review' %}warning{% elif item.estudo.status == 'finished' %}success{% else %}secondary{% endif %}">
                {{ item.estudo.get_status_display }}
              </span>
            </div>
            <p><strong>Início:</strong> {{ item.estudo.start_date|default:"Não definido" }} | <strong>Meta:</strong> {{ item.estudo.exam_date|default:"Não definida" }}</p>
            <p><strong>Progresso:</strong> {{ item.progresso }}% ({{ item.total_topics }} tópicos)</p>

            <!-- Mapa visual -->
            <div class="map-container position-relative" style="height: 80px; background: #2a2a3e; border-radius: 0.75rem; padding: 10px;">
              <div class="progress" style="height: 10px; background: #444; border-radius: 5px; margin-top: 20px;">
                <div class="progress-bar bg-primary" role="progressbar" style="width: {{ item.progresso }}%;" aria-valuenow="{{ item.progresso }}" aria-valuemin="0" aria-valuemax="100"></div>
              </div>
              <!-- Boneco 🏃 -->
              <div class="position-absolute" style="left: {{ item.progresso }}%; top: 10px; transform: translateX(-50%); font-size: 2rem;">
                🏃
              </div>
              <!-- Marcadores de início e fim -->
              <div class="position-absolute" style="left: 0%; top: 40px; font-size: 0.8rem; color: #aaa;">Início</div>
              <div class="position-absolute" style="right: 0%; top: 40px; font-size: 0.8rem; color: #aaa;">Meta</div>
            </div>
          </div>
        </div>
      </div>
    {% endfor %}
  </div>
{% else %}
  <div class="alert alert-info">Nenhum estudo cadastrado. <a href="{% url 'contests:create' %}" class="alert-link">Crie seu primeiro estudo</a>.</div>
{% endif %}
{% endblock %}
EOF

# 6. Atualizar base.html: ajustar navbar (menor padding e fonte) e adicionar link para Geral
cat > templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}StudySystem{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/style.css' %}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
  {% block extra_css %}{% endblock %}
</head>
<body>
  <div class="d-flex" id="wrapper">
    <!-- Sidebar -->
    <div class="bg-dark text-white" id="sidebar-wrapper">
      <div class="sidebar-heading text-center py-3 fs-5 fw-bold text-uppercase border-bottom">
        <i class="bi bi-mortarboard-fill"></i> StudySystem
      </div>
      <div class="list-group list-group-flush my-2">
        <a href="{% url 'dashboard:index' %}" class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'index' %}active{% endif %}">
          <i class="bi bi-speedometer2 me-2"></i> Dashboard
        </a>
        <a href="{% url 'contests:general' %}" class="list-group-item list-group-item-action {% if 'general' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-globe2 me-2"></i> Geral
        </a>
        <a href="{% url 'contests:list' %}" class="list-group-item list-group-item-action {% if 'contests' in request.resolver_match.app_name and not 'general' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-briefcase me-2"></i> Estudos
        </a>
        <a href="{% url 'subjects:list' %}" class="list-group-item list-group-item-action {% if 'subjects' in request.resolver_match.app_name %}active{% endif %}">
          <i class="bi bi-book me-2"></i> Matérias
        </a>
        <a href="{% url 'notes:list' %}" class="list-group-item list-group-item-action {% if 'notes' in request.resolver_match.app_name %}active{% endif %}">
          <i class="bi bi-sticky me-2"></i> Notas
        </a>
        <a href="{% url 'study:timer' %}" class="list-group-item list-group-item-action {% if 'study' in request.resolver_match.app_name %}active{% endif %}">
          <i class="bi bi-clock me-2"></i> Cronômetro
        </a>
        <a href="#" class="list-group-item list-group-item-action">
          <i class="bi bi-card-checklist me-2"></i> Flashcards
        </a>
        <a href="#" class="list-group-item list-group-item-action">
          <i class="bi bi-question-circle me-2"></i> Questões
        </a>
        <a href="#" class="list-group-item list-group-item-action">
          <i class="bi bi-calendar me-2"></i> Calendário
        </a>
        <a href="#" class="list-group-item list-group-item-action">
          <i class="bi bi-bar-chart me-2"></i> Estatísticas
        </a>
      </div>
    </div>
    <!-- Page Content -->
    <div id="page-content-wrapper" class="w-100">
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark border-bottom border-secondary">
        <div class="container-fluid">
          <button class="btn btn-outline-light" id="menu-toggle">
            <i class="bi bi-list"></i>
          </button>
          <div class="ms-auto d-flex align-items-center">
            <span class="me-3 text-light">
              <i class="bi bi-person-circle me-1"></i> {{ user.username }}
            </span>
            <a href="{% url 'accounts:logout' %}" class="btn btn-outline-danger btn-sm">
              <i class="bi bi-box-arrow-right me-1"></i> Sair
            </a>
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

# 7. Atualizar list.html – mudar labels
cat > templates/contests/list.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2><i class="bi bi-briefcase me-2"></i>Meus Estudos</h2>
  <a href="{% url 'contests:create' %}" class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i> Novo Estudo
  </a>
</div>

<div class="row g-4">
  {% for contest in contests %}
    <div class="col-md-4 col-lg-3">
      <div class="card h-100">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start">
            <h5 class="card-title">{{ contest.name }}</h5>
            <span class="badge bg-{% if contest.status == 'studying' %}primary{% elif contest.status == 'review' %}warning{% elif contest.status == 'finished' %}success{% else %}secondary{% endif %}">
              {{ contest.get_status_display }}
            </span>
          </div>
          <p class="card-text text-muted small">
            <i class="bi bi-building me-1"></i> {{ contest.organization|default:"-" }}<br>
            <i class="bi bi-person me-1"></i> {{ contest.position|default:"-" }}
          </p>
          <p class="card-text">
            <i class="bi bi-calendar-event me-1"></i> 
            {{ contest.exam_date|default:"Data não definida" }}
          </p>
          <div class="d-flex justify-content-between mt-3">
            <a href="{% url 'contests:detail' contest.pk %}" class="btn btn-sm btn-outline-primary">
              <i class="bi bi-eye"></i>
            </a>
            <a href="{% url 'contests:update' contest.pk %}" class="btn btn-sm btn-outline-secondary">
              <i class="bi bi-pencil"></i>
            </a>
            <a href="{% url 'contests:delete' contest.pk %}" class="btn btn-sm btn-outline-danger">
              <i class="bi bi-trash"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  {% empty %}
    <div class="col-12">
      <div class="alert alert-info" role="alert">
        <i class="bi bi-info-circle me-2"></i> Nenhum estudo cadastrado. 
        <a href="{% url 'contests:create' %}" class="alert-link">Criar o primeiro</a>
      </div>
    </div>
  {% endfor %}
</div>
{% endblock %}
EOF

# 8. Atualizar form.html – incluir start_date e labels
cat > templates/contests/form.html << 'EOF'
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-8">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h4 class="mb-0"><i class="bi bi-plus-circle me-2"></i>{% if object %}Editar Estudo{% else %}Novo Estudo{% endif %}</h4>
      </div>
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

# 9. Atualizar CSS para ajustar tamanho dos botões da sidebar
cat > static/css/style.css << 'EOF'
/* ===== GERAL ===== */
:root {
  --primary: #7c8cff;
  --primary-dark: #5a6adf;
  --primary-light: #a8b4ff;
  --sidebar-bg: #12121f;
  --sidebar-text: #c0c8e0;
  --sidebar-hover: #1e1e3a;
  --bg-body: #0f0f1a;
  --card-bg: #1a1a2e;
  --card-border: #2a2a3e;
  --card-shadow: 0 4px 15px rgba(0,0,0,0.5);
  --card-hover-shadow: 0 8px 25px rgba(0,0,0,0.7);
  --border-radius: 0.75rem;
  --text-light: #e8e8f0;
  --text-muted: #8a8aa0;
}

body {
  background-color: var(--bg-body);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  color: var(--text-light);
}

/* ===== SIDEBAR ===== */
#sidebar-wrapper {
  background: var(--sidebar-bg);
  min-height: 100vh;
  margin-left: -280px;
  transition: margin 0.3s ease-in-out;
  width: 280px;
  box-shadow: 2px 0 15px rgba(0,0,0,0.5);
  z-index: 1000;
}

#wrapper.toggled #sidebar-wrapper {
  margin-left: 0;
}

.sidebar-heading {
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #fff;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding: 1rem 1rem; /* menor padding */
  font-size: 1.1rem; /* menor fonte */
}

.sidebar-heading i {
  margin-right: 10px;
  color: var(--primary-light);
}

.list-group-item {
  border: none;
  border-radius: 0.5rem;
  margin: 0.2rem 0.5rem; /* reduzido */
  padding: 0.5rem 0.8rem; /* reduzido */
  background: transparent;
  color: var(--sidebar-text);
  transition: all 0.2s;
  font-weight: 500;
  font-size: 0.9rem; /* menor */
}

.list-group-item i {
  width: 1.5rem;
  font-size: 1rem; /* menor */
  color: var(--primary-light);
}

.list-group-item:hover {
  background: var(--sidebar-hover);
  color: #fff;
}

.list-group-item.active {
  background: var(--primary);
  color: #fff;
}

.list-group-item.active i {
  color: #fff;
}

/* ===== PAGE CONTENT ===== */
#page-content-wrapper {
  min-width: 0;
  width: 100%;
  transition: all 0.3s;
}

/* ===== NAVBAR ===== */
.navbar {
  background: #1a1a2e !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  padding: 0.5rem 1rem;
}

.navbar .btn-outline-light {
  border-color: #555;
  color: #ddd;
  padding: 0.25rem 0.6rem;
  font-size: 0.9rem;
}

.navbar .btn-outline-light:hover {
  background: #333;
  border-color: #777;
}

.navbar .btn-outline-danger {
  padding: 0.2rem 0.8rem;
  font-size: 0.85rem;
}

/* ===== CARDS ===== */
.card {
  border: 1px solid var(--card-border);
  border-radius: var(--border-radius);
  box-shadow: var(--card-shadow);
  transition: transform 0.2s, box-shadow 0.2s;
  background: var(--card-bg);
  color: var(--text-light);
}

.card:hover {
  box-shadow: var(--card-hover-shadow);
  transform: translateY(-3px);
}

.card .card-title {
  font-weight: 600;
  color: #c8d0e8;
  font-size: 0.95rem;
  letter-spacing: 0.02em;
}

.card .display-6 {
  font-weight: 700;
  color: var(--primary-light);
}

.card .card-body small {
  color: var(--text-muted);
}

/* ===== BOTÕES ===== */
.btn-primary {
  background: var(--primary);
  border: none;
  border-radius: 0.5rem;
  padding: 0.4rem 1rem;
  font-weight: 500;
  color: #fff;
}

.btn-primary:hover {
  background: var(--primary-dark);
  color: #fff;
}

.btn-outline-primary {
  border-color: var(--primary);
  color: var(--primary);
}

.btn-outline-primary:hover {
  background: var(--primary);
  color: #fff;
}

.btn-secondary, .btn-outline-secondary {
  border-color: #555;
  color: #ccc;
}

.btn-secondary:hover, .btn-outline-secondary:hover {
  background: #444;
  border-color: #666;
  color: #fff;
}

.btn-success {
  background: #28a745;
  border: none;
}

.btn-danger {
  background: #dc3545;
  border: none;
}

.btn-warning {
  background: #ffc107;
  border: none;
  color: #000;
}

/* ===== FORMULÁRIOS ===== */
.form-control, .form-select {
  border-radius: 0.5rem;
  border: 1px solid #333;
  background: #1e1e32;
  color: #e8e8f0;
  padding: 0.5rem 0.8rem;
}

.form-control:focus, .form-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(124, 140, 255, 0.2);
  background: #252545;
  color: #fff;
}

label {
  font-weight: 500;
  color: #c0c8e0;
}

/* ===== BADGES ===== */
.badge {
  border-radius: 0.5rem;
  padding: 0.3rem 0.7rem;
  font-weight: 500;
}

/* ===== PROGRESS ===== */
.progress {
  border-radius: 0.5rem;
  height: 0.7rem;
  background: #2a2a3e;
}

.progress-bar {
  background: var(--primary);
  border-radius: 0.5rem;
}

/* ===== LIST GROUP ===== */
.list-group-item {
  background: #1a1a2e;
  border: 1px solid #2a2a3e;
  color: #c8d0e8;
  border-radius: 0.5rem;
  margin-bottom: 0.25rem;
}

/* ===== MAPA ===== */
.map-container {
  background: #1a1a2e;
  border-radius: 0.75rem;
  padding: 10px;
}

/* ===== RESPONSIVIDADE ===== */
@media (min-width: 768px) {
  #sidebar-wrapper {
    margin-left: 0;
  }
  #wrapper.toggled #sidebar-wrapper {
    margin-left: -280px;
  }
}

@media (max-width: 767.98px) {
  #sidebar-wrapper {
    margin-left: -280px;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 1050;
  }
  #wrapper.toggled #sidebar-wrapper {
    margin-left: 0;
  }
  #page-content-wrapper {
    padding-top: 0;
  }
}
EOF

# 10. Atualizar dashboard para incluir link para geral
# (opcional, mas vou adicionar um card)
cat > templates/dashboard/index.html << 'EOF'
{% extends 'base.html' %}
{% load static %}
{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="row g-4">
  <!-- Cards -->
  <div class="col-md-3 col-sm-6">
    <div class="card h-100">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
          <h5 class="card-title">Hoje</h5>
          <i class="bi bi-clock-history fs-3 text-primary"></i>
        </div>
        <p class="display-6 fw-bold">{{ hours_today }}h</p>
        <small class="text-muted">Meta: {{ daily_goal_hours }}h</small>
      </div>
    </div>
  </div>

  <div class="col-md-3 col-sm-6">
    <div class="card h-100">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
          <h5 class="card-title">Semana</h5>
          <i class="bi bi-calendar-week fs-3 text-success"></i>
        </div>
        <p class="display-6 fw-bold">{{ hours_week }}h</p>
        <small class="text-muted">Últimos 7 dias</small>
      </div>
    </div>
  </div>

  <div class="col-md-3 col-sm-6">
    <div class="card h-100">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
          <h5 class="card-title">Mês</h5>
          <i class="bi bi-calendar-month fs-3 text-warning"></i>
        </div>
        <p class="display-6 fw-bold">{{ hours_month }}h</p>
        <small class="text-muted">Últimos 30 dias</small>
      </div>
    </div>
  </div>

  <div class="col-md-3 col-sm-6">
    <div class="card h-100">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
          <h5 class="card-title">Questões</h5>
          <i class="bi bi-check2-circle fs-3 text-info"></i>
        </div>
        <p class="display-6 fw-bold">{{ questions_today }}</p>
        <small class="text-muted">Acertos: {{ accuracy }}%</small>
      </div>
    </div>
  </div>
</div>

<!-- Segunda linha -->
<div class="row g-4 mt-2">
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title"><i class="bi bi-graph-up-arrow me-2"></i>Progresso Geral</h5>
        <div class="progress mb-3">
          <div class="progress-bar" role="progressbar" style="width: {{ progress_general }}%;" aria-valuenow="{{ progress_general }}" aria-valuemin="0" aria-valuemax="100">{{ progress_general }}%</div>
        </div>
        <div class="d-flex justify-content-between">
          <span><i class="bi bi-fire text-danger me-1"></i> Streak: {{ streak }} dias</span>
          <span><i class="bi bi-clock text-warning me-1"></i> Revisões: {{ reviews_pending }}</span>
        </div>
      </div>
    </div>
  </div>

  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title"><i class="bi bi-clock-history me-2"></i>Últimas Sessões</h5>
        <ul class="list-group list-group-flush">
          {% for session in last_sessions %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span><i class="bi bi-file-text me-2"></i>{{ session.topic.name|default:"Sem tópico" }}</span>
              <span class="badge bg-primary rounded-pill">{{ session.duration_minutes }} min</span>
            </li>
          {% empty %}
            <li class="list-group-item text-muted">Nenhuma sessão registrada.</li>
          {% endfor %}
        </ul>
      </div>
    </div>
  </div>
</div>

<!-- Botão para Visão Geral -->
<div class="row mt-4">
  <div class="col-12 text-center">
    <a href="{% url 'contests:general' %}" class="btn btn-primary btn-lg">
      <i class="bi bi-globe2 me-2"></i> Ver Visão Geral de Todos os Estudos
    </a>
  </div>
</div>
{% endblock %}
EOF

echo "✅ Sistema atualizado para Estudos Gerais com mapa!"
echo "Agora execute as migrações:"
echo "  python manage.py makemigrations"
echo "  python manage.py migrate"
echo "  python manage.py runserver"
