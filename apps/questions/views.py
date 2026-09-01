import json
import csv
import io
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum, Case, When, Value, FloatField, ExpressionWrapper, F
from django.utils import timezone
from .models import Question, QuestionAttempt, QuestionReview, ErrorLog, Simulated, SimulatedQuestion
from .forms import QuestionForm
from apps.subjects.models import Topic, Subject
from apps.contests.models import Contest

# ============================
# BANCO DE QUESTÕES
# ============================

class QuestionBankView(LoginRequiredMixin, ListView):
    model = Question
    template_name = 'questions/bank.html'
    context_object_name = 'questions'
    paginate_by = 20

    def get_queryset(self):
        qs = Question.objects.filter(user=self.request.user)
        # Filtros...
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
            qs = qs.filter(Q(enunciado__icontains=search) | Q(explicacao__icontains=search))

        order = self.request.GET.get('order', '-created_at')
        qs = qs.order_by(order)
        qs = qs.annotate(
            total_tentativas=Count('questionattempt'),
            acertos=Count('questionattempt', filter=Q(questionattempt__correta=True)),
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

# ============================
# CRUD DE QUESTÕES (COM FORMULÁRIO)
# ============================

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

# ============================
# RESOLUÇÃO DE QUESTÕES
# ============================

@login_required
def resolve_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    if request.method == 'POST':
        resposta = request.POST.get('resposta')
        if resposta:
            acertou = (resposta == question.alternativa_correta)
            QuestionAttempt.objects.create(
                user=request.user,
                question=question,
                resposta_escolhida=resposta,
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
                    defaults={'proxima_revisao': timezone.now().date() + timedelta(days=1), 'intervalo': 1}
                )
                if not created:
                    review.proxima_revisao = timezone.now().date() + timedelta(days=review.intervalo)
                    review.intervalo = min(review.intervalo * 2, 30)
                    review.vezes_revisado += 1
                    review.save()
            else:
                ErrorLog.objects.filter(user=request.user, question=question).delete()
                QuestionReview.objects.filter(user=request.user, question=question).delete()
            return JsonResponse({
                'acertou': acertou,
                'correta': question.alternativa_correta,
                'explicacao': question.explicacao,
            })
    context = {'question': question}
    return render(request, 'questions/resolve.html', context)

# ============================
# TREINO INTELIGENTE
# ============================

@login_required
def treino_inteligente(request):
    # ... (mantido igual)
    pass

@login_required
def treino_sessao(request):
    # ... (mantido igual)
    pass

# ============================
# SIMULADOS
# ============================

class SimuladoCreateView(LoginRequiredMixin, CreateView):
    # ... (mantido igual)
    pass

class SimuladoListView(LoginRequiredMixin, ListView):
    # ... (mantido igual)
    pass

@login_required
def simulado_iniciar(request, pk):
    # ... (mantido igual)
    pass

@login_required
def simulado_resolver(request, pk):
    # ... (mantido igual)
    pass

@login_required
def simulado_responder(request, pk):
    # ... (mantido igual)
    pass

@login_required
def simulado_finalizar(request, pk):
    # ... (mantido igual)
    pass

# ============================
# CADERNO DE ERROS
# ============================

@login_required
def error_log_list(request):
    errors = ErrorLog.objects.filter(user=request.user).select_related('question', 'question__topic', 'question__topic__subject')
    context = {'errors': errors}
    return render(request, 'questions/error_log.html', context)

@login_required
def error_log_detail(request, pk):
    error = get_object_or_404(ErrorLog, pk=pk, user=request.user)
    return render(request, 'questions/error_log_detail.html', {'error': error})

# ============================
# ANÁLISE DE DESEMPENHO
# ============================

@login_required
def performance(request):
    # ... (mantido igual)
    pass

# ============================
# IMPORTAÇÃO
# ============================

@login_required
def import_questions(request):
    # ... (mantido igual)
    pass
from .forms import QuestionForm

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

from .forms import QuestionForm

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
# ============================
# RESOLUÇÃO DE QUESTÕES
# ============================

from .models import Question, QuestionAttempt, ErrorLog, QuestionReview
from django.contrib import messages

@login_required
def resolve_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    resultado = None
    acertou = False
    resposta_usuario = None

    if request.method == 'POST':
        resposta_usuario = request.POST.get('resposta')
        if resposta_usuario:
            acertou = (resposta_usuario == question.alternativa_correta)
            # Registrar tentativa
            QuestionAttempt.objects.create(
                user=request.user,
                question=question,
                resposta_escolhida=resposta_usuario,
                correta=acertou,
                tempo_gasto=0,  # você pode capturar o tempo via JavaScript
                modo='treino',
                contest=question.contest,
                topic=question.topic,
            )
            if not acertou:
                # Registrar erro
                ErrorLog.objects.create(
                    user=request.user,
                    question=question,
                    motivo='desconhecido',  # pode ser preenchido depois
                    erro_consecutivo=1,
                )
                # Agendar revisão
                review, created = QuestionReview.objects.get_or_create(
                    user=request.user,
                    question=question,
                    defaults={'proxima_revisao': timezone.now().date() + timedelta(days=1), 'intervalo': 1}
                )
                if not created:
                    review.proxima_revisao = timezone.now().date() + timedelta(days=review.intervalo)
                    review.intervalo = min(review.intervalo * 2, 30)
                    review.vezes_revisado += 1
                    review.save()
            else:
                # Se acertou, remove do caderno de erros (se existir)
                ErrorLog.objects.filter(user=request.user, question=question).delete()
                QuestionReview.objects.filter(user=request.user, question=question).delete()

            resultado = True

    context = {
        'question': question,
        'resultado': resultado,
        'acertou': acertou,
        'resposta_usuario': resposta_usuario,
    }
    return render(request, 'questions/resolve.html', context)
