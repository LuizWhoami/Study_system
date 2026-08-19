from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from .models import Contest
from apps.subjects.models import Subject, Topic
from .forms import ContestForm
import json

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

# ============================
# PÁGINA GERAL DE ESTUDOS
# ============================
class GeneralView(LoginRequiredMixin, ListView):
    model = Contest
    template_name = 'contests/general.html'
    context_object_name = 'estudos'

    def get_queryset(self):
        return Contest.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        hoje = timezone.now().date()

        estudos_data = []
        for estudo in context['estudos']:
            # --- Cálculo do progresso por matéria ---
            subjects = Subject.objects.filter(contest=estudo)
            total_materias = subjects.count()
            progresso_materias = []

            for subject in subjects:
                total_topicos = Topic.objects.filter(subject=subject).count()
                topicos_concluidos = Topic.objects.filter(
                    subject=subject,
                    status__in=['mastered', 'studied']
                ).count()
                if total_topicos > 0:
                    progresso_materia = round((topicos_concluidos / total_topicos) * 100, 1)
                else:
                    # Matéria sem tópicos: progresso 0%
                    progresso_materia = 0.0
                progresso_materias.append(progresso_materia)

            # Progresso geral é a média dos progressos das matérias
            if total_materias > 0:
                progresso_geral = round(sum(progresso_materias) / total_materias, 1)
            else:
                progresso_geral = 0.0

            # Total de tópicos e concluídos (para exibição)
            total_topics = Topic.objects.filter(subject__contest=estudo).count()
            concluidos = Topic.objects.filter(
                subject__contest=estudo,
                status__in=['mastered', 'studied']
            ).count()

            # Data de início (created_at do concurso)
            data_inicio = estudo.created_at.date() if estudo.created_at else hoje
            data_prova = estudo.exam_date

            if data_prova and data_inicio:
                dias_totais = (data_prova - data_inicio).days
                dias_passados = (hoje - data_inicio).days
                if dias_totais > 0:
                    posicao_boneco = min(100, max(0, round((dias_passados / dias_totais) * 100)))
                else:
                    posicao_boneco = 0
            else:
                dias_totais = None
                dias_passados = None
                posicao_boneco = 0

            estudos_data.append({
                'estudo': estudo,
                'total_materias': total_materias,
                'progresso_materias': progresso_materias,
                'progresso': progresso_geral,
                'total_topics': total_topics,
                'concluidos': concluidos,
                'data_inicio': data_inicio,
                'data_prova': data_prova,
                'dias_totais': dias_totais,
                'dias_passados': dias_passados,
                'posicao_boneco': posicao_boneco,
            })

        context['estudos_data'] = estudos_data
        return context
