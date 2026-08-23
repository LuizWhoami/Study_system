from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
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
