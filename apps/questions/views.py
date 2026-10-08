"""
Views do app `questions`.

NOTA HISTÓRICA — 2026-10-08
---------------------------
Este arquivo foi limpo após um merge que empilhou 3 cópias de si mesmo.
Antes tinha 619 linhas; agora tem ~290. Bugs corrigidos:

  1) `Count('questionattempt')` → `Count('attempts')`
     relacionado ao `related_name` que a migration 0002 adiciona.
  2) `Q(questionattempt__correta=...)` → `Q(attempts__correta=...)`
  3) `questionreview__proxima_revisao` → `reviews__proxima_revisao`

Também foram removidas as duplicatas:
  - QuestionCreateView  (3x)
  - QuestionUpdateView  (2x)
  - resolve_question    (3x)
  - error_log_list      (2x)
  - treino_inteligente  (2x)
"""
import json
import csv
import io
from datetime import date, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView, View,
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import (
    Q, Count, Avg, Sum,
    Case, When, Value, FloatField, ExpressionWrapper, F,
)
from django.utils import timezone

from .models import (
    Question, QuestionAttempt, QuestionReview, ErrorLog,
    Simulated, SimulatedQuestion,
)
from .forms import QuestionForm
from apps.subjects.models import Topic, Subject
from apps.contests.models import Contest


# ============================================================
# BANCO DE QUESTÕES
# ============================================================

class QuestionBankView(LoginRequiredMixin, ListView):
    model = Question
    template_name = 'questions/bank.html'
    context_object_name = 'questions'
    paginate_by = 20

    def get_queryset(self):
        qs = Question.objects.filter(user=self.request.user)

        topic = self.request.GET.get('topic')
        subject = self.request.GET.get('subject')
        contest = self.request.GET.get('contest')
        difficulty = self.request.GET.get('dificuldade')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')

        if topic:
            qs = qs.filter(topic_id=topic)
        if subject:
            qs = qs.filter(topic__subject_id=subject)
        if contest:
            qs = qs.filter(contest_id=contest)
        if difficulty:
            qs = qs.filter(dificuldade=difficulty)
        if status == 'active':
            qs = qs.filter(status=True)
        elif status == 'inactive':
            qs = qs.filter(status=False)
        if search:
            qs = qs.filter(
                Q(enunciado__icontains=search) | Q(explicacao__icontains=search)
            )

        order = self.request.GET.get('order', '-created_at')
        qs = qs.order_by(order)
        qs = qs.annotate(
            total_tentativas=Count('attempts'),
            acertos=Count('attempts', filter=Q(attempts__correta=True)),
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topics'] = Topic.objects.filter(subject__contest__user=self.request.user)
        context['subjects'] = Subject.objects.filter(contest__user=self.request.user)
        context['contests'] = Contest.objects.filter(user=self.request.user)
        context['difficulties'] = Question.DIFFICULTY_CHOICES
        context['filters'] = self.request.GET
        return context


# ============================================================
# CRUD DE QUESTÕES
# ============================================================

class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'questions/form.html'
    success_url = reverse_lazy('questions:bank')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Questão criada com sucesso!')
        return super().form_valid(form)


class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'questions/form.html'
    success_url = reverse_lazy('questions:bank')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Questão atualizada com sucesso!')
        return super().form_valid(form)


class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    model = Question
    template_name = 'questions/confirm_delete.html'
    success_url = reverse_lazy('questions:bank')

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user)


# ============================================================
# RESOLUÇÃO DE QUESTÃO (avulsa, fora do treino)
# ============================================================

@login_required
def resolve_question(request, pk):
    """Resolve uma questão avulsa e mostra o feedback na mesma página."""
    question = get_object_or_404(Question, pk=pk, user=request.user)

    resultado = None
    acertou = False
    resposta_usuario = None

    if request.method == 'POST':
        resposta_usuario = request.POST.get('resposta')
        if resposta_usuario:
            acertou = (resposta_usuario == question.alternativa_correta)

            QuestionAttempt.objects.create(
                user=request.user,
                question=question,
                resposta_escolhida=resposta_usuario,
                correta=acertou,
                tempo_gasto=request.POST.get('tempo', 0),
                modo='treino',
                contest=question.contest,
                topic=question.topic,
            )

            if not acertou:
                ErrorLog.objects.create(
                    user=request.user,
                    question=question,
                    motivo=request.POST.get('motivo', 'desconhecido'),
                )
                review, created = QuestionReview.objects.get_or_create(
                    user=request.user,
                    question=question,
                    defaults={
                        'proxima_revisao': timezone.now().date() + timedelta(days=1),
                        'intervalo': 1,
                    },
                )
                if not created:
                    review.proxima_revisao = timezone.now().date() + timedelta(days=review.intervalo)
                    review.intervalo = min(review.intervalo * 2, 30)
                    review.vezes_revisado += 1
                    review.save()
            else:
                ErrorLog.objects.filter(user=request.user, question=question).delete()
                QuestionReview.objects.filter(user=request.user, question=question).delete()

            resultado = True

    return render(request, 'questions/resolve.html', {
        'question': question,
        'resultado': resultado,
        'acertou': acertou,
        'resposta_usuario': resposta_usuario,
    })

# ============================================================
# TREINO INTELIGENTE
# ============================================================

@login_required
def treino_inteligente(request):
    """
    Tela de configuração do treino.

    POST: monta a lista de questões segundo a estratégia escolhida,
          salva os IDs na sessão e redireciona para `treino_sessao`.

    Estratégias suportadas:
      - erros             → questões com mais erros acumulados
      - nunca_respondidas → questões sem nenhuma tentativa
      - atrasadas         → questões com revisão vencida
      - baixo_desempenho  → questões com taxa de acerto < 50%
      - aleatorio         → shuffle puro
    """
    if request.method == 'POST':
        materia_id = request.POST.get('materia')
        topico_id = request.POST.get('topico')
        quantidade = int(request.POST.get('quantidade', 10))
        dificuldade = request.POST.getlist('dificuldade')
        estrategia = request.POST.get('estrategia')

        qs = Question.objects.filter(user=request.user, status=True)

        if materia_id:
            qs = qs.filter(topic__subject_id=materia_id)
        if topico_id:
            qs = qs.filter(topic_id=topico_id)
        if dificuldade:
            qs = qs.filter(dificuldade__in=dificuldade)

        # ---- Estratégias ----
        # relacionamentos corretos:
        #   QuestionAttempt.question  → related_name='attempts'
        #   QuestionReview.question   → related_name='reviews'
        if estrategia == 'erros':
            qs = qs.annotate(
                total_erros=Count('attempts', filter=Q(attempts__correta=False))
            ).order_by('-total_erros')

        elif estrategia == 'nunca_respondidas':
            qs = qs.annotate(total=Count('attempts')).filter(total=0)

        elif estrategia == 'atrasadas':
            qs = qs.filter(reviews__proxima_revisao__lte=date.today())

        elif estrategia == 'baixo_desempenho':
            qs = qs.annotate(
                total=Count('attempts'),
                acertos=Count('attempts', filter=Q(attempts__correta=True)),
                taxa=Case(
                    When(total=0, then=Value(0.0)),
                    default=ExpressionWrapper(
                        F('acertos') * 100.0 / F('total'),
                        output_field=FloatField(),
                    ),
                ),
            ).filter(taxa__lt=50.0)

        else:  # aleatorio
            qs = qs.order_by('?')

        questoes = list(qs[:quantidade])

        if not questoes:
            messages.warning(
                request,
                'Nenhuma questão encontrada com os critérios selecionados.',
            )
            return redirect('questions:treino_inteligente')

        request.session['treino_questoes'] = [q.id for q in questoes]
        request.session['treino_indice'] = 0
        return redirect('questions:treino_sessao')

    # ---- GET: formulário de configuração ----
    subjects = Subject.objects.filter(contest__user=request.user)
    topics = Topic.objects.filter(subject__contest__user=request.user)
    difficulty_choices = Question.DIFFICULTY_CHOICES
    estrategias = [
        ('erros', 'Questões com mais erros'),
        ('nunca_respondidas', 'Questões nunca respondidas'),
        ('atrasadas', 'Revisões atrasadas'),
        ('baixo_desempenho', 'Tópicos com baixo desempenho'),
        ('aleatorio', 'Aleatório'),
    ]

    return render(request, 'questions/treino_config.html', {
        'subjects': subjects,
        'topics': topics,
        'difficulty_choices': difficulty_choices,
        'estrategias': estrategias,
    })


@login_required
def treino_sessao(request):
    """
    Renderiza a questão atual do treino.

    - GET simples: mostra a questão atual.
    - GET ?next=1: avança o índice (usado pelo botão "Próxima questão"
      após o feedback). Se chegar ao fim, encerra o treino.
    """
    if 'treino_questoes' not in request.session:
        messages.warning(request, 'Nenhum treino em andamento.')
        return redirect('questions:treino_inteligente')

    questoes_ids = request.session.get('treino_questoes', [])
    indice = request.session.get('treino_indice', 0)

    # Avanço explícito (vindo do "Próxima questão")
    if request.GET.get('next') == '1':
        indice += 1
        request.session['treino_indice'] = indice

    if indice >= len(questoes_ids):
        messages.success(request, 'Treino concluído! 🎉')
        request.session.pop('treino_questoes', None)
        request.session.pop('treino_indice', None)
        return redirect('questions:treino_inteligente')

    question = get_object_or_404(Question, pk=questoes_ids[indice], user=request.user)

    total = len(questoes_ids)
    return render(request, 'questions/treino_sessao.html', {
        'question': question,
        'indice': indice + 1,
        'total': total,
        'progresso': int(indice / total * 100) if total else 0,
    })


@login_required
def treino_responder(request):
    """
    Recebe a resposta, registra tentativa e re-renderiza a MESMA questão
    com o feedback (acertou/errou). O avanço acontece em `treino_sessao`
    quando o usuário clica em "Próxima questão" (?next=1).
    """
    if request.method != 'POST':
        return redirect('questions:treino_inteligente')

    question_id = request.POST.get('question_id')
    resposta = request.POST.get('resposta')
    tempo = int(request.POST.get('tempo', 0) or 0)

    if not question_id or not resposta:
        messages.error(request, 'Resposta inválida.')
        return redirect('questions:treino_sessao')

    question = get_object_or_404(Question, id=question_id, user=request.user)
    acertou = (resposta == question.alternativa_correta)

    QuestionAttempt.objects.create(
        user=request.user,
        question=question,
        resposta_escolhida=resposta,
        correta=acertou,
        tempo_gasto=tempo,
        modo='treino',
        contest=question.contest,
        topic=question.topic,
    )

    if not acertou:
        ErrorLog.objects.create(
            user=request.user,
            question=question,
            motivo=request.POST.get('motivo', 'desconhecido'),
        )
        review, created = QuestionReview.objects.get_or_create(
            user=request.user,
            question=question,
            defaults={
                'proxima_revisao': timezone.now().date() + timedelta(days=1),
                'intervalo': 1,
            },
        )
        if not created:
            review.proxima_revisao = timezone.now().date() + timedelta(days=review.intervalo)
            review.intervalo = min(review.intervalo * 2, 30)
            review.vezes_revisado += 1
            review.save()
    else:
        ErrorLog.objects.filter(user=request.user, question=question).delete()
        QuestionReview.objects.filter(user=request.user, question=question).delete()

    # Re-renderiza a MESMA questão com o feedback
    questoes_ids = request.session.get('treino_questoes', [])
    indice = request.session.get('treino_indice', 0)
    total = len(questoes_ids)
    progresso = int(indice / total * 100) if total else 0

    return render(request, 'questions/treino_sessao.html', {
        'question': question,
        'indice': indice + 1,
        'total': total,
        'progresso': progresso,
        'resultado': True,
        'acertou': acertou,
        'resposta_usuario': resposta,
    })

# ============================================================
# SIMULADOS — STUBS
# ============================================================
# TODO: implementar. Hoje retornam 501 para não quebrar o menu.
# Quando implementar, criar templates:
#   - questions/simulado_list.html
#   - questions/simulado_form.html
#   - questions/simulado_sessao.html
#   - questions/simulado_resultado.html

class SimuladoCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Simulados ainda não implementados.', status=501)


class SimuladoListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Simulados ainda não implementados.', status=501)


@login_required
def simulado_iniciar(request, pk):
    return HttpResponse('Simulados ainda não implementados.', status=501)


@login_required
def simulado_resolver(request, pk):
    return HttpResponse('Simulados ainda não implementados.', status=501)


@login_required
def simulado_responder(request, pk):
    return HttpResponse('Simulados ainda não implementados.', status=501)


@login_required
def simulado_finalizar(request, pk):
    return HttpResponse('Simulados ainda não implementados.', status=501)


# ============================================================
# CADERNO DE ERROS
# ============================================================

@login_required
def error_log_list(request):
    errors = (
        ErrorLog.objects
        .filter(user=request.user)
        .select_related('question', 'question__topic', 'question__topic__subject')
    )
    return render(request, 'questions/error_log.html', {'errors': errors})


@login_required
def error_log_detail(request, pk):
    error = get_object_or_404(ErrorLog, pk=pk, user=request.user)
    return render(request, 'questions/error_log_detail.html', {'error': error})


# ============================================================
# ANÁLISE DE DESEMPENHO — STUB
# ============================================================

@login_required
def performance(request):
    return HttpResponse('Análise de desempenho ainda não implementada.', status=501)


# ============================================================
# IMPORTAÇÃO — STUB
# ============================================================

@login_required
def import_questions(request):
    return HttpResponse('Importação de questões ainda não implementada.', status=501)


# ============================================================
# GERAÇÃO DE QUESTÕES COM IA (Groq)
# ============================================================

@login_required
def ia_gerar_page(request):
    """Página de geração de questões com IA."""
    contests = Contest.objects.filter(user=request.user).order_by('name')
    return render(request, 'questions/ia_gerar.html', {
        'contests': contests,
        'difficulty_choices': Question.DIFFICULTY_CHOICES,
    })


@login_required
@require_http_methods(['POST'])
def ia_gerar_api(request):
    """
    POST recebe:
      topic_id      (int, obrigatório)
      quantidade    (int, 1-10, default 5)
      dificuldade   (int, 1-5, default 3)
      fonte         ('auto' | 'notas', default 'auto')
    """
    from .services import gerar_e_salvar_questoes_ia
    from apps.subjects.models import Topic

    topic_id = request.POST.get('topic_id')
    if not topic_id:
        return JsonResponse({'success': False, 'error': 'Tópico não informado.'}, status=400)

    try:
        quantidade = int(request.POST.get('quantidade', 5))
        dificuldade = int(request.POST.get('dificuldade', 3))
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Valores numéricos inválidos.'}, status=400)

    fonte = request.POST.get('fonte', 'auto')
    banca = (request.POST.get('banca') or '').strip() or None

    try:
        topic = Topic.objects.select_related('subject', 'subject__contest').get(
            id=topic_id, subject__contest__user=request.user
        )
    except Topic.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tópico não encontrado.'}, status=404)

    try:
        resultado = gerar_e_salvar_questoes_ia(
            user=request.user,
            topic=topic,
            quantidade=quantidade,
            dificuldade=dificuldade,
            fonte=fonte,
            banca=banca,
        )
    except RuntimeError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        logger.exception('Erro inesperado ao gerar questões com IA')
        return JsonResponse(
            {'success': False, 'error': f'Erro inesperado: {exc}'},
            status=500,
        )

    criadas = resultado['criadas']
    if not criadas:
        return JsonResponse({
            'success': False,
            'error': 'A IA respondeu, mas nenhuma questão passou na validação.',
            'descartadas': resultado['descartadas'],
        }, status=422)

    return JsonResponse({
        'success': True,
        'criadas': len(criadas),
        'descartadas': resultado['descartadas'],
        'question_ids': [q.id for q in criadas],
        'fonte_usada': resultado['fonte_usada'],
        'banca': banca or 'genérica',
    })
