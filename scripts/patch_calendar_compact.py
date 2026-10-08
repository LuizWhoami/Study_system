#!/usr/bin/env python3
"""
Aplica o patch do calendário compacto:
  - Envolve o grid num .calendar-wrap (max-width 780px)
  - Troca <h4> do número do dia por <div>
  - Simplifica card-body
  - Valida que não sobrou h4 nem estrutura antiga
"""
import sys
from pathlib import Path

# Garante que o projeto está no PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.patch_helper import FilePatch, exit_ok  # noqa: E402


HTML = 'templates/calendar/calendar.html'


def main() -> bool:
    p = FilePatch(HTML)

    p.replace(
        '<div class="calendar-grid mb-4">',
        '<div class="calendar-wrap">\n  <div class="calendar-grid">',
        label='envolver grid em .calendar-wrap',
    )

    p.replace_flexible(
        '''      </div>
    {% endfor %}
  </div>

  {# ============ LEGENDA ============ #}''',
        '''      </div>
    {% endfor %}
  </div>
</div>

{# ============ LEGENDA ============ #}''',
        label='fechar .calendar-wrap antes da legenda',
    )

    p.replace(
        '<div class="calendar-day__number h4 mb-1">{{ day.day }}</div>',
        '<div class="calendar-day__number">{{ day.day }}</div>',
        label='trocar h4 por div (tamanho agora vem do CSS)',
    )

    p.replace(
        '<div class="card-body p-2 text-center d-flex flex-column justify-content-center">',
        '<div class="card-body">',
        label='simplificar card-body (padding vem do CSS)',
    )

    # Validações pós-patch
    p.assert_contains('calendar-wrap',          label='.calendar-wrap presente')
    p.assert_contains('calendar-day__number">', label='div do número limpa')
    p.assert_not_contains('<h4 class="calendar-day__number', label='<h4> antigo removido')

    return p.commit()


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    if dry:
        print('Modo DRY-RUN (nada será escrito)')
    ok = main() if not dry else FilePatch(HTML, dry_run=True) and main()
    exit_ok([ok])
