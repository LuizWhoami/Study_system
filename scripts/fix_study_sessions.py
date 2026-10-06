"""
Saneia sessões antigas ANTES de aplicar a constraint.

Uso:
    python manage.py shell < scripts/fix_study_sessions.py

O que faz:
1. Sessões com end_time preenchido → status='FINISHED'
2. Se um usuário tem mais de uma sessão sem end_time:
   mantém a MAIS RECENTE como RUNNING, o resto vira FINISHED.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_system.settings')
django.setup()

from django.utils import timezone
from apps.study.models import StudySession


def main():
    print('Saneando StudySession...')

    # 1. Sessões que já terminaram
    updated_finished = StudySession.objects.filter(
        end_time__isnull=False
    ).exclude(status=StudySession.STATUS_FINISHED).update(
        status=StudySession.STATUS_FINISHED
    )
    print(f'  → {updated_finished} sessão(ões) marcadas como FINISHED (tinham end_time)')

    # 2. Múltiplas "ativas" por usuário
    user_ids = StudySession.objects.filter(
        end_time__isnull=True
    ).values_list('user_id', flat=True).distinct()

    fixed = 0
    for uid in user_ids:
        sessions = list(
            StudySession.objects.filter(user_id=uid, end_time__isnull=True)
            .order_by('-start_time')
        )
        if len(sessions) <= 1:
            # uma só: garante status coerente
            s = sessions[0]
            if s.status != StudySession.STATUS_RUNNING:
                s.status = StudySession.STATUS_RUNNING
                s.save()
            continue
        # mantém a primeira (mais recente) como RUNNING, resto FINISHED
        keep = sessions[0]
        keep.status = StudySession.STATUS_RUNNING
        keep.save()
        for s in sessions[1:]:
            s.status = StudySession.STATUS_FINISHED
            s.end_time = s.end_time or s.start_time
            s.save()
            fixed += 1

    print(f'  → {fixed} sessão(ões) órfãs marcadas como FINISHED')
    print('Saneamento concluído.')


main()
