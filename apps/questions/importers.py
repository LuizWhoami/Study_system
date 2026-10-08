"""
Parser e validador de CSV de questões.

Formato esperado (cabeçalho obrigatório na 1ª linha):

    enunciado,alternativa_a,alternativa_b,alternativa_c,alternativa_d,correta,explicacao,banca,ano,dificuldade,topic_id

Colunas obrigatórias:
    enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, correta

Colunas opcionais:
    explicacao, banca, ano, dificuldade, topic_id
"""
from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from typing import Iterable, Optional

from django.apps import apps as django_apps

logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = {
    'enunciado',
    'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d',
    'correta',
}
OPTIONAL_COLUMNS = {'explicacao', 'banca', 'ano', 'dificuldade', 'topic_id'}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB
VALID_LETRAS = {'a', 'b', 'c', 'd'}


# ============================================================
# Estruturas
# ============================================================
@dataclass
class RowResult:
    line: int
    data: dict
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass
class ImportResult:
    rows: list[RowResult]
    total: int = 0
    valid: int = 0
    invalid: int = 0

    def __post_init__(self):
        self.total = len(self.rows)
        self.valid = sum(1 for r in self.rows if r.valid)
        self.invalid = self.total - self.valid


class CSVImportError(Exception):
    """Erro fatal — arquivo inteiro rejeitado antes de processar linhas."""


# ============================================================
# Leitura
# ============================================================
def _decode_file(file_obj) -> str:
    """Tenta utf-8-sig, senão latin-1. Devolve o texto."""
    raw = file_obj.read()
    if len(raw) > MAX_FILE_BYTES:
        raise CSVImportError(
            f'Arquivo muito grande ({len(raw)} bytes). Limite: {MAX_FILE_BYTES} bytes.'
        )
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise CSVImportError('Não foi possível decodificar o arquivo. Use UTF-8 ou Latin-1.')


def _check_header(fieldnames: list[str]) -> None:
    if not fieldnames:
        raise CSVImportError('CSV sem cabeçalho.')
    present = {f.strip().lower() for f in fieldnames if f}
    missing = REQUIRED_COLUMNS - present
    if missing:
        raise CSVImportError(
            'Colunas obrigatórias ausentes: ' + ', '.join(sorted(missing))
        )


# ============================================================
# Validação de linha
# ============================================================
def _validate_row(raw: dict, user, fallback_topic) -> RowResult:
    data = {k.strip().lower(): (v or '').strip() for k, v in raw.items() if k}
    errors: list[str] = []

    # Campos de texto obrigatórios
    for col in ('enunciado', 'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d'):
        if not data.get(col):
            errors.append(f'{col} vazio')

    # Correta
    correta = (data.get('correta') or '').lower()
    if correta not in VALID_LETRAS:
        errors.append(f'correta inválida: "{correta}" (use a, b, c ou d)')

    # Dificuldade (opcional, 1-5)
    dificuldade = 3
    if data.get('dificuldade'):
        try:
            dificuldade = int(data['dificuldade'])
            if not 1 <= dificuldade <= 5:
                errors.append(f'dificuldade fora de 1-5: {dificuldade}')
                dificuldade = 3
        except ValueError:
            errors.append(f'dificuldade não numérica: "{data["dificuldade"]}"')

    # Ano (opcional)
    ano = None
    if data.get('ano'):
        try:
            ano = int(data['ano'])
            if ano < 1900 or ano > 2100:
                errors.append(f'ano fora do intervalo: {ano}')
                ano = None
        except ValueError:
            errors.append(f'ano não numérico: "{data["ano"]}"')

    # Tópico
    topic = None
    if data.get('topic_id'):
        try:
            topic_id = int(data['topic_id'])
        except ValueError:
            errors.append(f'topic_id não numérico: "{data["topic_id"]}"')
        else:
            Topic = django_apps.get_model('subjects', 'Topic')
            topic = Topic.objects.filter(
                id=topic_id, subject__contest__user=user
            ).first()
            if not topic:
                errors.append(f'topic_id {topic_id} não encontrado ou não é seu')
    if topic is None:
        topic = fallback_topic
    if topic is None:
        errors.append('sem tópico (informe topic_id no CSV ou escolha um na tela)')

    return RowResult(
        line=0,
        data={
            'enunciado':        data.get('enunciado', ''),
            'alternativa_a':    data.get('alternativa_a', '')[:500],
            'alternativa_b':    data.get('alternativa_b', '')[:500],
            'alternativa_c':    data.get('alternativa_c', '')[:500],
            'alternativa_d':    data.get('alternativa_d', '')[:500],
            'alternativa_correta': correta if correta in VALID_LETRAS else 'a',
            'explicacao':       data.get('explicacao', ''),
            'banca':            data.get('banca', '')[:100],
            'ano':              ano,
            'dificuldade':      dificuldade,
            'topic':            topic,
        },
        errors=errors,
    )


# ============================================================
# Parser público
# ============================================================
def parse_csv(file_obj, user, fallback_topic=None) -> ImportResult:
    """
    Lê o CSV, valida cada linha e devolve ImportResult.

    Não grava nada no banco — quem grava é a view, após checar erros.
    Levanta CSVImportError se o arquivo inteiro é inválido (cabeçalho, encoding).
    """
    text = _decode_file(file_obj)
    reader = csv.DictReader(io.StringIO(text))

    _check_header(reader.fieldnames or [])

    rows: list[RowResult] = []
    for idx, raw in enumerate(reader, start=2):  # linha 1 = cabeçalho
        result = _validate_row(raw, user, fallback_topic)
        result.line = idx
        rows.append(result)

    return ImportResult(rows=rows)


# ============================================================
# Persistência
# ============================================================
def save_valid_rows(rows: Iterable[RowResult], user) -> int:
    """Grava as linhas válidas. Devolve o total criado."""
    Question = django_apps.get_model('questions', 'Question')

    criadas = 0
    for r in rows:
        if not r.valid:
            continue
        d = r.data
        topic = d['topic']
        Question.objects.create(
            user=user,
            topic=topic,
            contest=topic.subject.contest,
            enunciado=d['enunciado'],
            alternativa_a=d['alternativa_a'],
            alternativa_b=d['alternativa_b'],
            alternativa_c=d['alternativa_c'],
            alternativa_d=d['alternativa_d'],
            alternativa_correta=d['alternativa_correta'],
            explicacao=d['explicacao'],
            banca=d['banca'],
            ano=d['ano'],
            dificuldade=d['dificuldade'],
            status=True,
        )
        criadas += 1
    return criadas
