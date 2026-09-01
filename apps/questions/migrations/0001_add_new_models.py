from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('questions', '__first__'),  # Isso garante que a migração seja aplicada após a tabela Question existir
        ('contests', '__first__'),
        ('subjects', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resposta_escolhida', models.CharField(max_length=1)),
                ('correta', models.BooleanField()),
                ('data', models.DateTimeField(auto_now_add=True)),
                ('tempo_gasto', models.PositiveIntegerField(default=0, help_text='Tempo em segundos')),
                ('modo', models.CharField(choices=[('treino', 'Treino'), ('simulado', 'Simulado')], default='treino', max_length=20)),
                ('contest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contests.contest')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.question')),
                ('topic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='subjects.topic')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
            ],
            options={
                'ordering': ['-data'],
                'indexes': [
                    models.Index(fields=['user', 'question'], name='questions_questionattempt_user_id_question_id_idx'),
                    models.Index(fields=['user', 'correta'], name='questions_questionattempt_user_id_correta_idx'),
                    models.Index(fields=['user', 'data'], name='questions_questionattempt_user_id_data_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='QuestionReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proxima_revisao', models.DateField()),
                ('intervalo', models.PositiveIntegerField(default=1)),
                ('vezes_revisado', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user', 'proxima_revisao'], name='questions_questionreview_user_id_proxima_revisao_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.CharField(choices=[('desconhecido', 'Não conhecia o conteúdo'), ('esqueci', 'Esqueci'), ('confundi', 'Confundi conceitos'), ('interpretacao', 'Errei por interpretação'), ('desatencao', 'Desatenção'), ('chute', 'Chutei'), ('outro', 'Outro')], default='desconhecido', max_length=20)),
                ('data', models.DateTimeField(auto_now_add=True)),
                ('erro_consecutivo', models.PositiveSmallIntegerField(default=1)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
            ],
            options={
                'ordering': ['-data'],
                'indexes': [
                    models.Index(fields=['user', 'question'], name='questions_errorlog_user_id_question_id_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='Simulated',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(blank=True, max_length=200)),
                ('quantidade', models.PositiveIntegerField()),
                ('tempo_limite', models.PositiveIntegerField(help_text='Tempo em minutos')),
                ('data_inicio', models.DateTimeField(auto_now_add=True)),
                ('data_fim', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('in_progress', 'Em andamento'), ('finished', 'Finalizado'), ('cancelled', 'Cancelado')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('contest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contests.contest')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
            ],
            options={
                'ordering': ['-data_inicio'],
                'indexes': [
                    models.Index(fields=['user', 'status'], name='questions_simulated_user_id_status_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='SimulatedQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordem', models.PositiveIntegerField()),
                ('resposta_escolhida', models.CharField(blank=True, max_length=1, null=True)),
                ('correta', models.BooleanField(blank=True, null=True)),
                ('tempo_gasto', models.PositiveIntegerField(default=0)),
                ('marcada', models.BooleanField(default=False)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.question')),
                ('simulated', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questoes', to='questions.simulated')),
            ],
            options={
                'ordering': ['ordem'],
                'unique_together': {('simulated', 'question')},
            },
        ),
    ]
