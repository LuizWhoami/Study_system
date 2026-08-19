#!/bin/bash
# estudar_fixed.sh - Configuração da página "Estudar"

set -e

echo "🚀 Configurando página 'Estudar'..."

# 1. Template study.html
cat > templates/study/study.html << 'HTML'
{% extends 'base.html' %}
{% load static %}
{% block title %}Estudar{% endblock %}

{% block extra_css %}
<style>
  .study-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 70vh;
  }
  .timer-display {
    font-size: 5rem;
    font-weight: 700;
    color: #7c8cff;
    letter-spacing: 0.05em;
    font-family: 'Inter', monospace;
    background: rgba(255,255,255,0.05);
    padding: 20px 40px;
    border-radius: 20px;
    border: 1px solid rgba(124, 140, 255, 0.2);
  }
  .study-buttons .btn {
    min-width: 120px;
    margin: 0 8px;
    border-radius: 50px;
    padding: 14px 35px;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s;
  }
  .study-buttons .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
  }
  .study-info {
    margin-top: 30px;
    font-size: 1.1rem;
    color: #c0c8e0;
  }
  .study-info .badge {
    font-size: 1rem;
    padding: 8px 16px;
  }
  .current-study {
    background: rgba(124, 140, 255, 0.1);
    border: 1px solid rgba(124, 140, 255, 0.2);
    padding: 12px 24px;
    border-radius: 12px;
    margin-bottom: 20px;
  }
  .current-study strong {
    color: #7c8cff;
  }
  .modal-content {
    background: #1a1a2e;
    border: 1px solid #2d2d44;
    border-radius: 16px;
    color: #e8e8f0;
  }
  .modal-header {
    border-bottom: 1px solid #2d2d44;
  }
  .modal-footer {
    border-top: 1px solid #2d2d44;
  }
  .modal-title {
    color: #7c8cff;
  }
  .modal .form-select, .modal .form-label {
    color: #e8e8f0;
  }
  .modal .form-select {
    background-color: #2d2d44;
    border-color: #3d3d5c;
    color: #fff;
  }
  .modal .form-select option {
    background-color: #1a1a2e;
  }
  .btn-close {
    filter: invert(1);
  }
  @media (max-width: 576px) {
    .timer-display {
      font-size: 3rem;
      padding: 15px 25px;
    }
    .study-buttons .btn {
      min-width: 90px;
      padding: 10px 20px;
      font-size: 0.9rem;
    }
  }
</style>
{% endblock %}

{% block content %}
<div class="study-container">
  <div class="current-study text-center" id="current-study-info">
    <span class="text-muted">Nenhum estudo em andamento</span>
  </div>
  <div class="timer-display" id="timer-display">00:00:00</div>
  <div class="study-buttons mt-4">
    <button type="button" class="btn btn-success" id="start-btn" data-bs-toggle="modal" data-bs-target="#studyModal">
      <i class="bi bi-play-fill me-1"></i> Iniciar
    </button>
    <button type="button" class="btn btn-warning" id="pause-btn" disabled>
      <i class="bi bi-pause-fill me-1"></i> Pausar
    </button>
    <button type="button" class="btn btn-danger" id="end-btn" disabled>
      <i class="bi bi-stop-fill me-1"></i> Finalizar
    </button>
  </div>
  <div class="study-info mt-4">
    <span id="session-timer" class="badge bg-secondary">Sessão: 0 min</span>
    <span id="topic-name" class="badge bg-primary ms-2">Tópico: --</span>
  </div>
</div>

<div class="modal fade" id="studyModal" tabindex="-1" aria-labelledby="studyModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="studyModalLabel"><i class="bi bi-book me-2"></i>O que você vai estudar?</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
      </div>
      <div class="modal-body">
        <form id="study-select-form">
          <div class="mb-3">
            <label for="estudo-select" class="form-label">Estudo</label>
            <select class="form-select" id="estudo-select" required>
              <option value="">Selecione...</option>
              {% for estudo in estudos %}
                <option value="{{ estudo.id }}">{{ estudo.name }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="mb-3">
            <label for="materia-select" class="form-label">Matéria</label>
            <select class="form-select" id="materia-select" disabled required>
              <option value="">Primeiro selecione um estudo</option>
            </select>
          </div>
          <div class="mb-3">
            <label for="topico-select" class="form-label">Tópico</label>
            <select class="form-select" id="topico-select" disabled required>
              <option value="">Primeiro selecione uma matéria</option>
            </select>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
        <button type="button" class="btn btn-primary" id="confirm-study-btn" disabled>
          <i class="bi bi-play-circle me-1"></i> Começar
        </button>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
  let timerInterval = null;
  let seconds = 0;
  let sessionId = null;
  let isRunning = false;
  let selectedTopicId = null;
  let selectedTopicName = '';
  const display = document.getElementById('timer-display');
  const startBtn = document.getElementById('start-btn');
  const pauseBtn = document.getElementById('pause-btn');
  const endBtn = document.getElementById('end-btn');
  const sessionTimer = document.getElementById('session-timer');
  const topicNameEl = document.getElementById('topic-name');
  const currentInfo = document.getElementById('current-study-info');
  const estudoSelect = document.getElementById('estudo-select');
  const materiaSelect = document.getElementById('materia-select');
  const topicoSelect = document.getElementById('topico-select');
  const confirmBtn = document.getElementById('confirm-study-btn');

  function formatTime(s) {
    const h = String(Math.floor(s / 3600)).padStart(2, '0');
    const m = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
    const sec = String(s % 60).padStart(2, '0');
    return `${h}:${m}:${sec}`;
  }
  function updateDisplay() {
    display.textContent = formatTime(seconds);
    sessionTimer.textContent = `Sessão: ${Math.floor(seconds / 60)} min`;
  }

  estudoSelect.addEventListener('change', function() {
    const estudoId = this.value;
    if (!estudoId) {
      materiaSelect.disabled = true;
      materiaSelect.innerHTML = '<option value="">Primeiro selecione um estudo</option>';
      topicoSelect.disabled = true;
      topicoSelect.innerHTML = '<option value="">Primeiro selecione uma matéria</option>';
      confirmBtn.disabled = true;
      return;
    }
    fetch(`/estudo/api/materias-por-estudo/${estudoId}/`)
      .then(response => response.json())
      .then(data => {
        materiaSelect.disabled = false;
        materiaSelect.innerHTML = '<option value="">Selecione...</option>';
        data.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m.id;
          opt.textContent = m.name;
          materiaSelect.appendChild(opt);
        });
        topicoSelect.disabled = true;
        topicoSelect.innerHTML = '<option value="">Primeiro selecione uma matéria</option>';
        confirmBtn.disabled = true;
      });
  });

  materiaSelect.addEventListener('change', function() {
    const materiaId = this.value;
    if (!materiaId) {
      topicoSelect.disabled = true;
      topicoSelect.innerHTML = '<option value="">Primeiro selecione uma matéria</option>';
      confirmBtn.disabled = true;
      return;
    }
    fetch(`/estudo/api/topicos-por-materia/${materiaId}/`)
      .then(response => response.json())
      .then(data => {
        topicoSelect.disabled = false;
        topicoSelect.innerHTML = '<option value="">Selecione...</option>';
        data.forEach(t => {
          const opt = document.createElement('option');
          opt.value = t.id;
          opt.textContent = t.name;
          topicoSelect.appendChild(opt);
        });
        confirmBtn.disabled = true;
      });
  });

  topicoSelect.addEventListener('change', function() {
    confirmBtn.disabled = !this.value;
    if (this.value) {
      selectedTopicName = this.options[this.selectedIndex].text;
    }
  });

  confirmBtn.addEventListener('click', function() {
    const topicoId = topicoSelect.value;
    if (!topicoId) return;
    const modal = bootstrap.Modal.getInstance(document.getElementById('studyModal'));
    modal.hide();
    fetch("{% url 'study:start_session' %}", {
      method: 'POST',
      headers: { 'X-CSRFToken': '{{ csrf_token }}' },
      body: new URLSearchParams({ topic: topicoId })
    })
    .then(response => response.json())
    .then(data => {
      sessionId = data.session_id;
      selectedTopicId = topicoId;
      currentInfo.innerHTML = `<strong>Estudando:</strong> ${selectedTopicName}`;
      topicNameEl.textContent = `Tópico: ${selectedTopicName}`;
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
  });

  pauseBtn.addEventListener('click', function() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
      isRunning = false;
      pauseBtn.innerHTML = '<i class="bi bi-play-fill me-1"></i> Continuar';
    } else {
      timerInterval = setInterval(() => {
        seconds++;
        updateDisplay();
      }, 1000);
      isRunning = true;
      pauseBtn.innerHTML = '<i class="bi bi-pause-fill me-1"></i> Pausar';
    }
  });

  endBtn.addEventListener('click', function() {
    if (timerInterval) clearInterval(timerInterval);
    if (sessionId) {
      fetch("{% url 'study:end_session' %}", {
        method: 'POST',
        headers: { 'X-CSRFToken': '{{ csrf_token }}' },
        body: new URLSearchParams({
          session_id: sessionId,
          duration_minutes: Math.floor(seconds / 60)
        })
      })
      .then(response => response.json())
      .then(data => {
        alert('✅ Sessão finalizada!');
        resetTimer();
        currentInfo.innerHTML = `<span class="text-muted">Nenhum estudo em andamento</span>`;
        topicNameEl.textContent = 'Tópico: --';
      });
    } else {
      resetTimer();
    }
  });

  function resetTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    seconds = 0;
    updateDisplay();
    isRunning = false;
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    endBtn.disabled = true;
    pauseBtn.innerHTML = '<i class="bi bi-pause-fill me-1"></i> Pausar';
    sessionId = null;
    selectedTopicId = null;
    selectedTopicName = '';
  }
</script>
{% endblock %}
HTML

# 2. Views
cat > apps/study/views.py << 'PY'
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import StudySession, DailyProgress
from apps.subjects.models import Subject, Topic
from apps.contests.models import Contest

@login_required
def study_view(request):
    estudos = Contest.objects.filter(user=request.user)
    return render(request, 'study/study.html', {'estudos': estudos})

@login_required
def api_materias_por_estudo(request, estudo_id):
    estudo = get_object_or_404(Contest, id=estudo_id, user=request.user)
    materias = Subject.objects.filter(contest=estudo).values('id', 'name')
    return JsonResponse(list(materias), safe=False)

@login_required
def api_topicos_por_materia(request, materia_id):
    materia = get_object_or_404(Subject, id=materia_id, contest__user=request.user)
    topicos = Topic.objects.filter(subject=materia).values('id', 'name')
    return JsonResponse(list(topicos), safe=False)

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
PY

# 3. URLs
cat > apps/study/urls.py << 'URL'
from django.urls import path
from . import views

app_name = 'study'
urlpatterns = [
    path('', views.study_view, name='study'),
    path('api/materias-por-estudo/<int:estudo_id>/', views.api_materias_por_estudo, name='api_materias'),
    path('api/topicos-por-materia/<int:materia_id>/', views.api_topicos_por_materia, name='api_topicos'),
    path('start/', views.start_session, name='start_session'),
    path('end/', views.end_session, name='end_session'),
]
URL

# 4. Atualizar sidebar
cp templates/base.html templates/base.html.bak 2>/dev/null || true
sed -i 's|{% url .study:timer. %}|{% url .study:study. %}|g' templates/base.html
sed -i 's|Cronômetro|Estudar|g' templates/base.html

echo "✅ Página 'Estudar' criada com sucesso!"
echo ""
echo "Agora execute:"
echo "  python manage.py runserver"
echo "E acesse: http://127.0.0.1:8000/estudo/"
