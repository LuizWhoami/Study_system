from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Subject, Topic
from .forms import SubjectForm, TopicForm
from apps.contests.models import Contest

# ============================
# VIEWS PARA MATÉRIAS (SUBJECT)
# ============================

class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'subjects/subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        return Subject.objects.filter(contest__user=self.request.user)

class SubjectByContestView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'subjects/by_contest.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        self.estudo = get_object_or_404(Contest, id=self.kwargs['estudo_id'], user=self.request.user)
        return Subject.objects.filter(contest=self.estudo)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estudo'] = self.estudo
        return context

class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        estudo_id = self.request.GET.get('estudo')
        if estudo_id:
            initial['contest'] = estudo_id
        return initial

    def form_valid(self, form):
        self.success_url = reverse('subjects:by_contest', kwargs={'estudo_id': form.instance.contest.id})
        return super().form_valid(form)

    def get_success_url(self):
        return self.success_url or reverse_lazy('subjects:list')

class SubjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/form.html'

    def get_queryset(self):
        return Subject.objects.filter(contest__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.success_url = reverse('subjects:by_contest', kwargs={'estudo_id': form.instance.contest.id})
        return super().form_valid(form)

    def get_success_url(self):
        return self.success_url or reverse_lazy('subjects:list')

class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = 'subjects/confirm_delete.html'
    success_url = reverse_lazy('subjects:list')

    def get_queryset(self):
        return Subject.objects.filter(contest__user=self.request.user)

# ============================
# VIEWS PARA TÓPICOS (ASSUNTOS)
# ============================

class TopicBySubjectView(LoginRequiredMixin, ListView):
    model = Topic
    template_name = 'subjects/topics_by_subject.html'
    context_object_name = 'topics'

    def get_queryset(self):
        self.materia = get_object_or_404(Subject, id=self.kwargs['subject_id'], contest__user=self.request.user)
        return Topic.objects.filter(subject=self.materia)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject'] = self.materia
        return context

class TopicCreateView(LoginRequiredMixin, CreateView):
    model = Topic
    form_class = TopicForm
    template_name = 'subjects/topic_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        materia_id = self.request.GET.get('materia')
        if materia_id:
            initial['subject'] = materia_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        materia_id = self.request.GET.get('materia')
        if materia_id:
            context['subject_id'] = materia_id
            # Gera a URL de volta com segurança
            context['back_url'] = reverse('subjects:topics_by_subject', kwargs={'subject_id': materia_id})
        else:
            context['back_url'] = '#'
        return context

    def form_valid(self, form):
        self.success_url = reverse('subjects:topics_by_subject', kwargs={'subject_id': form.instance.subject.id})
        return super().form_valid(form)

    def get_success_url(self):
        return self.success_url or reverse_lazy('subjects:list')

class TopicUpdateView(LoginRequiredMixin, UpdateView):
    model = Topic
    form_class = TopicForm
    template_name = 'subjects/topic_form.html'

    def get_queryset(self):
        return Topic.objects.filter(subject__contest__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.success_url = reverse('subjects:topics_by_subject', kwargs={'subject_id': form.instance.subject.id})
        return super().form_valid(form)

    def get_success_url(self):
        return self.success_url or reverse_lazy('subjects:list')

class TopicDeleteView(LoginRequiredMixin, DeleteView):
    model = Topic
    template_name = 'subjects/confirm_delete.html'
    success_url = reverse_lazy('subjects:list')

    def get_queryset(self):
        return Topic.objects.filter(subject__contest__user=self.request.user)

# ============================
# AÇÕES DE ALTERAÇÃO DE STATUS
# ============================

def alterar_status_materia(request, pk):
    subject = get_object_or_404(Subject, pk=pk, contest__user=request.user)
    novo_status = request.POST.get('status')
    if novo_status not in ['studying', 'mastered']:
        messages.error(request, 'Status inválido.')
        return redirect('subjects:by_contest', estudo_id=subject.contest.id)

    subject.status = novo_status
    subject.save()

    if novo_status == 'mastered':
        subject.topics.update(status='mastered')
    elif novo_status == 'studying':
        pass

    messages.success(request, f'Matéria "{subject.name}" alterada para {subject.get_status_display()}.')
    return redirect('subjects:by_contest', estudo_id=subject.contest.id)

def alterar_status_topico(request, pk):
    topic = get_object_or_404(Topic, pk=pk, subject__contest__user=request.user)
    novo_status = request.POST.get('status')
    if novo_status not in ['studying', 'mastered']:
        messages.error(request, 'Status inválido.')
        return redirect('subjects:topics_by_subject', subject_id=topic.subject.id)

    topic.status = novo_status
    topic.save()

    messages.success(request, f'Assunto "{topic.name}" alterado para {topic.get_status_display()}.')
    return redirect('subjects:topics_by_subject', subject_id=topic.subject.id)
