from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Question
from apps.subjects.models import Topic

class QuestionListView(LoginRequiredMixin, ListView):
    model = Question
    template_name = 'questions/list.html'
    context_object_name = 'questions'

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user).order_by('-created_at')

class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    template_name = 'questions/form.html'
    fields = ['topic', 'enunciado', 'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_correta', 'explicacao', 'dificuldade']
    success_url = reverse_lazy('questions:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    template_name = 'questions/form.html'
    fields = ['topic', 'enunciado', 'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_correta', 'explicacao', 'dificuldade']
    success_url = reverse_lazy('questions:list')

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user)

class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    model = Question
    template_name = 'questions/confirm_delete.html'
    success_url = reverse_lazy('questions:list')

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user)

class QuestionDetailView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = 'questions/detail.html'
    context_object_name = 'question'

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user)

@login_required
def responder_questao(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    if request.method == 'POST':
        alternativa_escolhida = request.POST.get('alternativa')
        if alternativa_escolhida:
            if alternativa_escolhida == question.alternativa_correta:
                messages.success(request, '✅ Resposta correta!')
            else:
                messages.error(request, f'❌ Resposta incorreta. A alternativa correta é {question.alternativa_correta.upper()}.')
        else:
            messages.warning(request, 'Selecione uma alternativa.')
        return redirect('questions:detail', pk=question.pk)
    return redirect('questions:list')

@login_required
def resolve_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    resultado = None
    acertou = False
    resposta_usuario = None

    if request.method == 'POST':
        resposta_usuario = request.POST.get('resposta')
        if resposta_usuario:
            if resposta_usuario == question.alternativa_correta:
                acertou = True
            else:
                acertou = False
            resultado = True

    context = {
        'question': question,
        'resultado': resultado,
        'acertou': acertou,
        'resposta_usuario': resposta_usuario,
    }
    return render(request, 'questions/resolve.html', context)

@login_required
def resolve_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    resultado = None
    acertou = False
    resposta_usuario = None

    if request.method == 'POST':
        resposta_usuario = request.POST.get('resposta')
        if resposta_usuario:
            if resposta_usuario == question.alternativa_correta:
                acertou = True
            else:
                acertou = False
            resultado = True

    context = {
        'question': question,
        'resultado': resultado,
        'acertou': acertou,
        'resposta_usuario': resposta_usuario,
    }
    return render(request, 'questions/resolve.html', context)

@login_required
def resolve_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    resultado = None
    acertou = False
    resposta_usuario = None

    if request.method == 'POST':
        resposta_usuario = request.POST.get('resposta')
        if resposta_usuario:
            if resposta_usuario == question.alternativa_correta:
                acertou = True
            else:
                acertou = False
            resultado = True

    context = {
        'question': question,
        'resultado': resultado,
        'acertou': acertou,
        'resposta_usuario': resposta_usuario,
    }
    return render(request, 'questions/resolve.html', context)
