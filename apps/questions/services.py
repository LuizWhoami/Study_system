"""
Serviço de geração de questões via IA (Groq).

Reaproveita `apps.core.services.GroqService` — NÃO cria um segundo cliente.
"""
import logging

from django.apps import apps as django_apps
from django.db import transaction

from apps.core.services import GroqService

logger = logging.getLogger(__name__)


# ============================================================
# COLETA DE TEXTO-FONTE
# ============================================================

def _coletar_texto_fonte(topic, fonte='auto'):
    """
    Retorna (texto_fonte, tipo_fonte).

    fonte:
      'notas' → só conteúdo das notas do tópico (erro se não houver)
      'auto'  → notas se houver; senão nome do tópico
    """
    Note = django_apps.get_model('notes', 'Note')

    notas_qs = Note.objects.filter(topic=topic).values_list('content', flat=True)[:10]
    textos = [n for n in notas_qs if n and n.strip()]
    texto_notas = "\n\n".join(textos).strip()

    if fonte == 'notas' and len(texto_notas) < 50:
        raise RuntimeError(
            'Este tópico não tem notas suficientes para gerar questões. '
            'Adicione conteúdo às notas ou use o modo "auto".'
        )

    if len(texto_notas) >= 50:
        logger.info(
            "Gerando questões para '%s' a partir de %d nota(s).",
            topic.name, len(textos),
        )
        return texto_notas, 'notas'

    partes = [
        getattr(topic.subject.contest, 'name', ''),
        getattr(topic.subject, 'name', ''),
        topic.name,
    ]
    texto_base = " > ".join(p for p in partes if p)
    logger.info("Sem notas suficientes, usando nome do tópico: %s", texto_base)
    return texto_base, 'nome_topico'


# ============================================================
# GERAÇÃO + PERSISTÊNCIA
# ============================================================

@transaction.atomic
def gerar_e_salvar_questoes_ia(user, topic, quantidade=5, dificuldade=3, fonte='auto', banca=None):
    """
    Gera questões via Groq e persiste como `Question`.
    """
    quantidade = max(1, min(int(quantidade), 10))
    dificuldade = max(1, min(int(dificuldade), 5))

    texto_fonte, tipo_fonte = _coletar_texto_fonte(topic, fonte=fonte)

    service = GroqService()
    if not service.enabled:
        raise RuntimeError(
            'Serviço de IA desabilitado. Verifique se GROQ_API_KEY está configurada.'
        )

    questoes_raw = service.gerar_questoes(texto_fonte, quantidade=quantidade, banca=banca)

    # Fallback: se a banca quebrou a geração, tenta de novo sem ela
    if not questoes_raw and banca:
        logger.warning(
            "Geração com banca=%s retornou vazio. Tentando sem banca...",
            banca,
        )
        questoes_raw = service.gerar_questoes(
            texto_fonte, quantidade=quantidade, banca=None,
        )
        if questoes_raw:
            logger.info(
                "Fallback sem banca funcionou (%d questões). "
                "Marcando banca como 'genérica'.",
                len(questoes_raw),
            )
            banca = None

    if not questoes_raw:
        raise RuntimeError(
            'A IA não retornou questões. Tente novamente ou adicione mais conteúdo ao tópico.'
        )

    from apps.questions.models import Question

    criadas = []
    descartadas = 0

    for q in questoes_raw:
        alt = q.get('alternativas') or {}
        if isinstance(alt, str):
            logger.warning("Alternativas vieram como string, descartando.")
            descartadas += 1
            continue

        a = (alt.get('a') or '').strip()
        b = (alt.get('b') or '').strip()
        c = (alt.get('c') or '').strip()
        d = (alt.get('d') or '').strip()

        if not all([a, b, c, d]):
            logger.warning("Questão sem as 4 alternativas — descartada.")
            descartadas += 1
            continue

        correta = (q.get('correta') or 'a').strip().lower()
        if correta not in ('a', 'b', 'c', 'd'):
            correta = 'a'

        enunciado = (q.get('enunciado') or '').strip()
        if not enunciado:
            descartadas += 1
            continue

        try:
            obj = Question.objects.create(
                user=user,
                topic=topic,
                contest=topic.subject.contest,
                enunciado=enunciado,
                alternativa_a=a[:500],
                alternativa_b=b[:500],
                alternativa_c=c[:500],
                alternativa_d=d[:500],
                alternativa_correta=correta,
                explicacao=(q.get('explicacao') or '').strip(),
                dificuldade=dificuldade,
                banca=(banca or '')[:100],
                status=True,
            )
        except Exception as exc:
            logger.error("Falha ao salvar questão: %s", exc)
            descartadas += 1
            continue

        criadas.append(obj)

    return {
        'criadas': criadas,
        'descartadas': descartadas,
        'fonte_usada': tipo_fonte,
        'preview': texto_fonte[:200],
    }
