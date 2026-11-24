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
        return (
            Contest.objects
            .filter(user=self.request.user)
            .prefetch_related('subjects__topics')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.localdate()

        estudos_data = []
        total_topicos_dominados = 0
        progressos_para_media = []

        for estudo in context['estudos']:
            subjects = list(estudo.subjects.all())
            total_materias = len(subjects)
            progresso_materias = []
            materias_foco = []
            total_topics = 0
            concluidos = 0
            dominados_estudo = 0

            for subject in subjects:
                topics = list(subject.topics.all())
                total_topicos = len(topics)
                topicos_concluidos = sum(1 for t in topics if t.status in ('mastered', 'studied'))
                dominados_subject = sum(1 for t in topics if t.status == 'mastered')

                total_topics += total_topicos
                concluidos += topicos_concluidos
                dominados_estudo += dominados_subject

                if total_topicos > 0:
                    progresso_materia = round((topicos_concluidos / total_topicos) * 100, 1)
                    pendentes = total_topicos - topicos_concluidos
                    if pendentes > 0:
                        materias_foco.append({
                            'nome': subject.name,
                            'pendentes': pendentes,
                            'total': total_topicos,
                            'progresso': progresso_materia,
                        })
                else:
                    progresso_materia = 0.0
                progresso_materias.append(progresso_materia)

            total_topicos_dominados += dominados_estudo
            materias_foco.sort(key=lambda x: -x['pendentes'])
            materias_foco = materias_foco[:2]

            if total_materias > 0:
                progresso_geral = round(sum(progresso_materias) / total_materias, 1)
            else:
                progresso_geral = 0.0

            if estudo.status in ('studying', 'review', 'intensive'):
                progressos_para_media.append(progresso_geral)

            data_inicio = estudo.created_at.date() if estudo.created_at else hoje
            data_prova = estudo.exam_date

            # Dias restantes + urgência
            dias_restantes = None
            urgencia = 'sem-data'
            if data_prova:
                delta = (data_prova - hoje).days
                dias_restantes = delta
                if delta < 0:
                    urgencia = 'vencida'
                elif delta <= 30:
                    urgencia = 'urgente'
                elif delta <= 90:
                    urgencia = 'atencao'
                else:
                    urgencia = 'normal'

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
                'materias_foco': materias_foco,
                'dias_restantes': dias_restantes,
                'urgencia': urgencia,
            })

        # Ordena: prova mais próxima primeiro; sem data / vencida no fim
        def sort_key(x):
            d = x['dias_restantes']
            if d is None:
                return (2, 0)
            if d < 0:
                return (2, d)
            return (0, d)
        estudos_data.sort(key=sort_key)

        # KPIs globais
        total_estudos = len(estudos_data)
        total_estudos_ativos = sum(
            1 for e in estudos_data
            if e['estudo'].status in ('studying', 'review', 'intensive')
        )
        progresso_medio = (
            round(sum(progressos_para_media) / len(progressos_para_media), 1)
            if progressos_para_media else 0
        )
        proxima_prova_dias = None
        for e in estudos_data:
            d = e['dias_restantes']
            if d is not None and d >= 0:
                proxima_prova_dias = d
                break

        context['estudos_data'] = estudos_data
        context['kpis'] = {
            'total_estudos': total_estudos,
            'total_estudos_ativos': total_estudos_ativos,
            'total_topicos_dominados': total_topicos_dominados,
            'progresso_medio': progresso_medio,
            'proxima_prova_dias': proxima_prova_dias,
        }
        return context

