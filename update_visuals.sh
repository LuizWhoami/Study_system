#!/bin/bash
# Atualiza o visual de todos os templates do LS Study

set -e
cd /var/www/Study_system

echo "🎨 Atualizando visuais dos templates..."

# ============================================
# CONTESTS - LISTA
# ============================================
cat > templates/contests/list.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Meus Estudos{% endblock %}
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
          <div class="d-flex justify-content-between align-items-start mb-2">
            <h5 class="card-title">{{ contest.name }}</h5>
            <span class="badge bg-{% if contest.status == 'studying' %}primary{% elif contest.status == 'review' %}warning{% elif contest.status == 'finished' %}success{% else %}secondary{% endif %}">
              {{ contest.get_status_display }}
            </span>
          </div>
          {% if contest.main_topic %}
            <p class="text-muted small mb-2"><i class="bi bi-tag me-1"></i>{{ contest.main_topic }}</p>
          {% endif %}
          <p class="text-muted small mb-2">
            <i class="bi bi-building me-1"></i> {{ contest.organization|default:"—" }}<br>
            <i class="bi bi-person me-1"></i> {{ contest.position|default:"—" }}
          </p>
          <p class="text-muted small mb-3">
            <i class="bi bi-calendar-event me-1"></i> {{ contest.exam_date|default:"Data não definida" }}
          </p>
          <div class="d-flex gap-2 flex-wrap">
            <a href="{% url 'contests:detail' contest.pk %}" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i></a>
            <a href="{% url 'subjects:by_contest' contest.pk %}" class="btn btn-sm btn-outline-info"><i class="bi bi-book"></i> Matérias</a>
            <a href="{% url 'contests:update' contest.pk %}" class="btn btn-sm btn-outline-secondary"><i class="bi bi-pencil"></i></a>
            <a href="{% url 'contests:delete' contest.pk %}" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></a>
          </div>
        </div>
      </div>
    </div>
  {% empty %}
    <div class="col-12">
      <div class="alert alert-info">
        <i class="bi bi-info-circle me-2"></i> Nenhum estudo cadastrado.
        <a href="{% url 'contests:create' %}" class="alert-link">Criar o primeiro</a>
      </div>
    </div>
  {% endfor %}
</div>
{% endblock %}
EOF

# ============================================
# CONTESTS - DETALHE
# ============================================
cat > templates/contests/detail.html << 'EOF'
{% extends 'base.html' %}
{% block title %}{{ contest.name }}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2>{{ contest.name }}</h2>
  <div class="d-flex gap-2">
    <a href="{% url 'contests:update' contest.pk %}" class="btn btn-warning"><i class="bi bi-pencil me-1"></i> Editar</a>
    <a href="{% url 'contests:list' %}" class="btn btn-secondary"><i class="bi bi-arrow-left me-1"></i> Voltar</a>
  </div>
</div>

<div class="card">
  <div class="card-body">
    <div class="row g-3">
      <div class="col-md-6"><strong>Órgão:</strong> {{ contest.organization|default:"—" }}</div>
      <div class="col-md-6"><strong>Cargo:</strong> {{ contest.position|default:"—" }}</div>
      <div class="col-md-6"><strong>Tópico principal:</strong> {{ contest.main_topic|default:"—" }}</div>
      <div class="col-md-6"><strong>Banca:</strong> {{ contest.board|default:"—" }}</div>
      <div class="col-md-6"><strong>Data da prova:</strong> {{ contest.exam_date|default:"Não definida" }}</div>
      <div class="col-md-6"><strong>Data prevista:</strong> {{ contest.expected_date|default:"—" }}</div>
      <div class="col-md-6"><strong>Status:</strong> {{ contest.get_status_display }}</div>
      <div class="col-md-6"><strong>Prioridade:</strong> {{ contest.priority }}</div>
      <div class="col-md-6"><strong>Meta de horas:</strong> {{ contest.goal_hours }}h</div>
      <div class="col-md-6"><strong>Meta de questões:</strong> {{ contest.goal_questions }}</div>
    </div>
    {% if contest.notes %}
      <hr>
      <strong>Observações:</strong>
      <p>{{ contest.notes|linebreaks }}</p>
    {% endif %}
  </div>
</div>
{% endblock %}
EOF

# ============================================
# SUBJECTS - LISTA GERAL
# ============================================
cat > templates/subjects/subject_list.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Matérias{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2><i class="bi bi-book me-2"></i>Todas as Matérias</h2>
  <a href="{% url 'subjects:create' %}" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> Nova Matéria</a>
</div>

<div class="row g-4">
  {% for subject in subjects %}
    <div class="col-md-4 col-lg-3">
      <div class="card h-100">
        <div class="card-body">
          <h5 class="card-title">{{ subject.name }}</h5>
          <p class="text-muted small mb-3"><i class="bi bi-briefcase me-1"></i> {{ subject.contest.name }}</p>
          <a href="{% url 'subjects:topics_by_subject' subject.id %}" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-list-ul me-1"></i> Assuntos
          </a>
        </div>
      </div>
    </div>
  {% empty %}
    <div class="col-12"><div class="alert alert-info">Nenhuma matéria cadastrada.</div></div>
  {% endfor %}
</div>
{% endblock %}
EOF

# ============================================
# SUBJECTS - POR ESTUDO
# ============================================
cat > templates/subjects/by_contest.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Matérias de {{ estudo.name }}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2><i class="bi bi-book me-2"></i>Matérias de {{ estudo.name }}</h2>
  <a href="{% url 'subjects:create' %}?estudo={{ estudo.id }}" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> Nova Matéria</a>
</div>

<div class="row g-4">
  {% for subject in subjects %}
    <div class="col-md-4">
      <div class="card h-100">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <h5 class="card-title">{{ subject.name }}</h5>
            <span class="badge bg-{% if subject.status == 'mastered' %}success{% elif subject.status == 'studying' %}primary{% else %}secondary{% endif %}">
              {{ subject.get_status_display }}
            </span>
          </div>
          <p class="text-muted small"><i class="bi bi-list-ul me-1"></i> {{ subject.topics.count }} assuntos</p>
          <div class="d-flex gap-2 flex-wrap">
            <a href="{% url 'subjects:topics_by_subject' subject.id %}" class="btn btn-sm btn-outline-primary"><i class="bi bi-list-ul me-1"></i> Assuntos</a>
            <a href="{% url 'subjects:update' subject.id %}" class="btn btn-sm btn-outline-secondary"><i class="bi bi-pencil"></i></a>
            <a href="{% url 'subjects:delete' subject.id %}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Excluir matéria?')"><i class="bi bi-trash"></i></a>
          </div>
        </div>
      </div>
    </div>
  {% empty %}
    <div class="col-12"><div class="alert alert-info">Nenhuma matéria cadastrada. <a href="{% url 'subjects:create' %}?estudo={{ estudo.id }}" class="alert-link">Adicionar</a></div></div>
  {% endfor %}
</div>

<a href="{% url 'contests:list' %}" class="btn btn-secondary mt-3"><i class="bi bi-arrow-left me-1"></i> Voltar</a>
{% endblock %}
EOF

# ============================================
# SUBJECTS - FORM
# ============================================
cat > templates/subjects/form.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Nova Matéria{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header"><h4 class="mb-0"><i class="bi bi-book me-2"></i>Nova Matéria</h4></div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          <div class="mb-3">
            <label class="form-label">Concurso/Estudo</label>
            {{ form.contest }}
          </div>
          <div class="mb-3">
            <label class="form-label">Nome da Matéria</label>
            {{ form.name }}
          </div>
          <div class="mb-3">
            <label class="form-label">Ordem</label>
            {{ form.order }}
          </div>
          <button type="submit" class="btn btn-success w-100"><i class="bi bi-save me-1"></i> Salvar</button>
          <a href="{% url 'subjects:list' %}" class="btn btn-secondary w-100 mt-2">Cancelar</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

# ============================================
# SUBJECTS - TOPICOS POR MATÉRIA
# ============================================
cat > templates/subjects/topics_by_subject.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Assuntos de {{ subject.name }}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2><i class="bi bi-diagram-2 me-2"></i>Assuntos de {{ subject.name }}</h2>
  <a href="{% url 'subjects:topic_create' %}?materia={{ subject.id }}" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> Novo Assunto</a>
</div>

<div class="row g-4">
  {% for topic in topics %}
    <div class="col-md-4">
      <div class="card h-100">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <h5 class="card-title">{{ topic.name }}</h5>
            <span class="badge bg-{% if topic.status == 'mastered' %}success{% elif topic.status == 'studying' %}primary{% else %}secondary{% endif %}">
              {{ topic.get_status_display }}
            </span>
          </div>
          <div class="d-flex gap-2 flex-wrap">
            <a href="{% url 'subjects:topic_update' topic.id %}" class="btn btn-sm btn-outline-secondary"><i class="bi bi-pencil"></i> Editar</a>
            <a href="{% url 'subjects:topic_delete' topic.id %}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Excluir assunto?')"><i class="bi bi-trash"></i> Excluir</a>
          </div>
        </div>
      </div>
    </div>
  {% empty %}
    <div class="col-12"><div class="alert alert-info">Nenhum assunto cadastrado.</div></div>
  {% endfor %}
</div>

<a href="{% url 'subjects:by_contest' subject.contest.id %}" class="btn btn-secondary mt-3"><i class="bi bi-arrow-left me-1"></i> Voltar</a>
{% endblock %}
EOF

# ============================================
# SUBJECTS - TOPIC FORM
# ============================================
cat > templates/subjects/topic_form.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Novo Assunto{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header"><h4 class="mb-0"><i class="bi bi-diagram-2 me-2"></i>Novo Assunto</h4></div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          <div class="mb-3"><label class="form-label">Matéria</label>{{ form.subject }}</div>
          <div class="mb-3"><label class="form-label">Nome do Assunto</label>{{ form.name }}</div>
          <div class="mb-3"><label class="form-label">Tópico pai (opcional)</label>{{ form.parent }}</div>
          <div class="mb-3"><label class="form-label">Status</label>{{ form.status }}</div>
          <div class="mb-3"><label class="form-label">Prioridade</label>{{ form.priority }}</div>
          <div class="mb-3"><label class="form-label">Ordem</label>{{ form.order }}</div>
          <button type="submit" class="btn btn-success w-100"><i class="bi bi-save me-1"></i> Salvar</button>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
EOF

# ============================================
# NOTES - LISTA
# ============================================
cat > templates/notes/list.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Notas{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2><i class="bi bi-sticky me-2"></i>Minhas Notas</h2>
  <a href="{% url 'notes:create' %}" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> Nova Nota</a>
</div>

<div class="row g-4">
  {% for note in notes %}
    <div class="col-md-4 col-lg-3">
      <div class="card h-100">
        <div class="card-body">
          <h5 class="card-title">{{ note.title }}</h5>
          <p class="text-muted small mb-2"><i class="bi bi-tag me-1"></i>{{ note.topic.name|default:"Sem tópico" }}</p>
          <p class="small mb-3">{{ note.content|truncatewords:15 }}</p>
          <div class="d-flex gap-2">
            <a href="{% url 'notes:detail' note.pk %}" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i></a>
            <a href="{% url 'notes:update' note.pk %}" class="btn btn-sm btn-outline-secondary"><i class="bi bi-pencil"></i></a>
            <a href="{% url 'notes:delete' note.pk %}" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></a>
          </div>
        </div>
      </div>
    </div>
  {% empty %}
    <div class="col-12"><div class="alert alert-info">Nenhuma nota criada. <a href="{% url 'notes:create' %}" class="alert-link">Criar a primeira</a></div></div>
  {% endfor %}
</div>
{% endblock %}
EOF

# ============================================
# NOTES - DETALHE
# ============================================
cat > templates/notes/detail.html << 'EOF'
{% extends 'base.html' %}
{% block title %}{{ note.title }}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2>{{ note.title }}</h2>
  <div class="d-flex gap-2">
    <a href="{% url 'notes:update' note.pk %}" class="btn btn-warning"><i class="bi bi-pencil me-1"></i> Editar</a>
    <a href="{% url 'notes:list' %}" class="btn btn-secondary"><i class="bi bi-arrow-left me-1"></i> Voltar</a>
  </div>
</div>

<p class="text-muted"><strong>Tópico:</strong> {{ note.topic.name|default:"Sem tópico" }}</p>

<div class="card">
  <div class="card-body">
    {{ note.content|linebreaks }}
  </div>
</div>

{% if note.tags.all %}
  <p class="mt-3">
    <strong>Tags:</strong>
    {% for tag in note.tags.all %}<span class="badge bg-secondary me-1">{{ tag.name }}</span>{% endfor %}
  </p>
{% endif %}
{% endblock %}
EOF

# ============================================
# FLASHCARDS - LISTA
# ============================================
cat > templates/flashcards/list.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Flashcards{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2><i class="bi bi-card-checklist me-2"></i>Flashcards de Hoje</h2>
  <a href="{% url 'flashcards:criar' %}" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> Novo Flashcard</a>
</div>

{% if total_pendentes == 0 %}
  <div class="alert alert-success"><i class="bi bi-check-circle me-2"></i> Nenhum flashcard pendente para hoje!</div>
{% else %}
  <p class="text-muted">Você tem <strong>{{ total_pendentes }}</strong> flashcards para revisar.</p>
  <div class="row g-4">
    {% for flashcard in flashcards %}
      <div class="col-md-4">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">{{ flashcard.pergunta|truncatewords:10 }}</h5>
            <p class="text-muted small mb-3"><i class="bi bi-tag me-1"></i>{{ flashcard.topic.subject.name }} → {{ flashcard.topic.name }}</p>
            <p class="small mb-3">
              <span class="badge bg-secondary">Revisões: {{ flashcard.vezes_revisado }}</span>
            </p>
            <a href="{% url 'flashcards:revisar' flashcard.pk %}" class="btn btn-sm btn-success w-100"><i class="bi bi-arrow-right-circle me-1"></i> Revisar</a>
          </div>
        </div>
      </div>
    {% endfor %}
  </div>
{% endif %}

<a href="{% url 'flashcards:estatisticas' %}" class="btn btn-secondary mt-3"><i class="bi bi-bar-chart me-1"></i> Ver estatísticas</a>
{% endblock %}
EOF

# ============================================
# QUESTIONS - BANCO DE QUESTÕES
# ============================================
cat > templates/questions/bank.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Banco de Questões{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
  <h2><i class="bi bi-database me-2"></i>Banco de Questões</h2>
  <div class="d-flex gap-2 flex-wrap">
    <a href="{% url 'questions:treino_inteligente' %}" class="btn btn-warning"><i class="bi bi-robot me-1"></i> Treino</a>
    <a href="{% url 'questions:error_log' %}" class="btn btn-danger"><i class="bi bi-journal-x me-1"></i> Caderno de Erros</a>
    <a href="{% url 'questions:create' %}" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> Nova Questão</a>
  </div>
</div>

<div class="card mb-4">
  <div class="card-body">
    <form method="get" class="row g-3">
      <div class="col-md-3">
        <label class="form-label">Matéria</label>
        <select name="subject" class="form-select">
          <option value="">Todas</option>
          {% for subject in subjects %}<option value="{{ subject.id }}" {% if request.GET.subject == subject.id|stringformat:'s' %}selected{% endif %}>{{ subject.name }}</option>{% endfor %}
        </select>
      </div>
      <div class="col-md-3">
        <label class="form-label">Tópico</label>
        <select name="topic" class="form-select">
          <option value="">Todos</option>
          {% for topic in topics %}<option value="{{ topic.id }}" {% if request.GET.topic == topic.id|stringformat:'s' %}selected{% endif %}>{{ topic.name }}</option>{% endfor %}
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label">Dificuldade</label>
        <select name="dificuldade" class="form-select">
          <option value="">Todas</option>
          {% for key, value in difficulties %}<option value="{{ key }}" {% if request.GET.dificuldade == key|stringformat:'s' %}selected{% endif %}>{{ value }}</option>{% endfor %}
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label">Status</label>
        <select name="status" class="form-select">
          <option value="">Todos</option>
          <option value="active" {% if request.GET.status == 'active' %}selected{% endif %}>Ativas</option>
          <option value="inactive" {% if request.GET.status == 'inactive' %}selected{% endif %}>Inativas</option>
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label">Busca</label>
        <input type="text" name="search" class="form-control" placeholder="Palavra-chave" value="{{ request.GET.search|default:'' }}">
      </div>
      <div class="col-12 text-end">
        <button type="submit" class="btn btn-primary">Filtrar</button>
        <a href="{% url 'questions:bank' %}" class="btn btn-secondary">Limpar</a>
      </div>
    </form>
  </div>
</div>

<div class="table-responsive">
  <table class="table">
    <thead>
      <tr><th>ID</th><th>Enunciado</th><th>Matéria</th><th>Dificuldade</th><th>Status</th><th class="text-center">Ações</th></tr>
    </thead>
    <tbody>
      {% for question in questions %}
        <tr>
          <td>{{ question.id }}</td>
          <td>{{ question.enunciado|truncatewords:10 }}</td>
          <td>{{ question.topic.subject.name|default:"—" }}</td>
          <td><span class="badge bg-{% if question.dificuldade <= 2 %}success{% elif question.dificuldade == 3 %}warning{% else %}danger{% endif %}">{{ question.get_dificuldade_display }}</span></td>
          <td>{% if question.status %}<span class="badge bg-success">Ativa</span>{% else %}<span class="badge bg-secondary">Inativa</span>{% endif %}</td>
          <td class="text-center">
            <div class="btn-group btn-group-sm">
              <a href="{% url 'questions:resolve' question.pk %}" class="btn btn-outline-primary"><i class="bi bi-play-fill"></i></a>
              <a href="{% url 'questions:update' question.pk %}" class="btn btn-outline-secondary"><i class="bi bi-pencil"></i></a>
              <a href="{% url 'questions:delete' question.pk %}" class="btn btn-outline-danger"><i class="bi bi-trash"></i></a>
            </div>
          </td>
        </tr>
      {% empty %}
        <tr><td colspan="6" class="text-center text-muted py-4">Nenhuma questão encontrada.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% if is_paginated %}
<nav class="mt-4">
  <ul class="pagination justify-content-center">
    {% if page_obj.has_previous %}
      <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Anterior</a></li>
    {% endif %}
    <li class="page-item active"><span class="page-link">{{ page_obj.number }} de {{ page_obj.paginator.num_pages }}</span></li>
    {% if page_obj.has_next %}
      <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Próxima</a></li>
    {% endif %}
  </ul>
</nav>
{% endif %}
{% endblock %}
EOF

# ============================================
# QUESTIONS - CADERNO DE ERROS
# ============================================
cat > templates/questions/error_log.html << 'EOF'
{% extends 'base.html' %}
{% block title %}Caderno de Erros{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2><i class="bi bi-journal-x me-2"></i>Caderno de Erros</h2>
  <span class="badge bg-danger">{{ errors|length }} erros</span>
</div>

{% if errors %}
  <div class="row g-4">
    {% for error in errors %}
      <div class="col-md-6 col-lg-4">
        <div class="card h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h5 class="card-title">{{ error.question.enunciado|truncatewords:8 }}</h5>
              <span class="badge bg-danger">{{ error.erro_consecutivo }}x</span>
            </div>
            <p class="text-muted small mb-2"><i class="bi bi-tag me-1"></i>{{ error.question.topic.subject.name|default:"—" }}</p>
            <p class="text-muted small mb-2"><i class="bi bi-calendar me-1"></i>{{ error.data|date:"d/m/Y" }}</p>
            <p class="small mb-3"><strong>Motivo:</strong> {{ error.get_motivo_display }}</p>
            <a href="{% url 'questions:resolve' error.question.id %}" class="btn btn-sm btn-outline-primary w-100"><i class="bi bi-arrow-repeat me-1"></i> Revisar</a>
          </div>
        </div>
      </div>
    {% endfor %}
  </div>
{% else %}
  <div class="alert alert-success"><i class="bi bi-check-circle me-2"></i> Nenhum erro registrado!</div>
{% endif %}

<a href="{% url 'questions:bank' %}" class="btn btn-secondary mt-3"><i class="bi bi-arrow-left me-1"></i> Voltar</a>
{% endblock %}
EOF

echo "✅ Visuais atualizados com sucesso!"
