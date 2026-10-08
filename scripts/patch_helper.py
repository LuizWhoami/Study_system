"""
Helper para aplicar patches em arquivos de texto.

Princípios:
  1. Falha explícita — operação `required` que não casa aborta o commit.
  2. Escrita atômica — só escreve se TODAS as ops required passaram.
  3. Matching resiliente — `replace_flexible` ignora diferenças de
     indentação/quebras de linha, sem perder o layout original.
  4. Relatório visual — ícones por op, sucesso/falha por arquivo.
  5. Exit code — `sys.exit(0)` em sucesso, `sys.exit(1)` se algo falhou.

Uso:
    from scripts.patch_helper import FilePatch

    p = FilePatch('caminho/arquivo.py')
    p.replace('antigo', 'novo', label='trocar import')
    p.replace_flexible('def x(): pass', 'def x(): return 1', label='reescrever x')
    ok = p.commit()
    if not ok:
        sys.exit(1)
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================
# Cor por status (ANSI, com fallback sem cor se não for tty)
# ============================================================
_TTY = sys.stdout.isatty()
def _c(code: str, s: str) -> str:
    return f'\033[{code}m{s}\033[0m' if _TTY else s

GREEN  = lambda s: _c('32', s)
RED    = lambda s: _c('31', s)
YELLOW = lambda s: _c('33', s)
BLUE   = lambda s: _c('34', s)
DIM    = lambda s: _c('2',  s)


# ============================================================
# Estruturas
# ============================================================
@dataclass
class Op:
    label:  str
    kind:   str
    status: str = 'pending'    # ok | not_found | skipped | error
    detail: str = ''

    @property
    def icon(self) -> str:
        return {
            'ok':        '✅',
            'not_found': '❌',
            'skipped':   '⏭️ ',
            'error':     '⚠️ ',
            'pending':   '⏳',
        }.get(self.status, '?')


@dataclass
class FilePatch:
    path: str
    dry_run: bool = False

    _original: str = field(default='', init=False)
    _current:  str = field(default='', init=False)
    _ops:      list[Op] = field(default_factory=list, init=False)
    _errors:   int = field(default=0, init=False)

    def __post_init__(self):
        self.path = Path(self.path)
        if not self.path.exists():
            raise FileNotFoundError(f'Arquivo não existe: {self.path}')
        self._original = self.path.read_text(encoding='utf-8')
        self._current  = self._original

    # ---------------- Operações ----------------

    def replace(self, old: str, new: str, label: str, *, required: bool = True) -> 'FilePatch':
        """Substituição literal. Falha se `old` não existir (quando required)."""
        if old not in self._current:
            self._record(label, 'replace', 'not_found' if required else 'skipped')
            self._errors += 1 if required else 0
            return self
        n = self._current.count(old)
        self._current = self._current.replace(old, new)
        self._record(label, 'replace', 'ok', f'{n}x')
        return self

    def replace_regex(self, pattern: str, replacement: str, label: str,
                      *, required: bool = True, flags: int = 0) -> 'FilePatch':
        """Substituição por regex."""
        new_str, n = re.subn(pattern, replacement, self._current, flags=flags)
        if n == 0:
            self._record(label, 'replace_regex', 'not_found' if required else 'skipped')
            self._errors += 1 if required else 0
            return self
        self._current = new_str
        self._record(label, 'replace_regex', 'ok', f'{n}x')
        return self

    def replace_flexible(self, old: str, new: str, label: str,
                         *, required: bool = True) -> 'FilePatch':
        """
        Substituição resiliente a diferenças de indentação/quebra de linha.
        Casa qualquer espaço em branco (\s+) entre tokens e preserva
        a indentação original do bloco no arquivo.
        """
        stripped = old.strip()
        if not stripped:
            self._record(label, 'replace_flexible', 'error', 'old vazio')
            self._errors += 1
            return self

        # Reconstrói um regex: cada bloco de espaços no `old` casa \s+
        parts = [re.escape(tok) for tok in stripped.split()]
        pattern = r'\s+'.join(parts)
        m = re.search(pattern, self._current)
        if not m:
            self._record(label, 'replace_flexible', 'not_found' if required else 'skipped')
            self._errors += 1 if required else 0
            return self

        # Detecta a indentação da linha onde o match começa
        line_start = self._current.rfind('\n', 0, m.start()) + 1
        indent = self._current[line_start:m.start()]

        # Aplica a mesma indentação às linhas do novo conteúdo
        new_lines = new.splitlines()
        if not new_lines:
            new_content = ''
        else:
            new_content = '\n'.join(
                (indent + ln) if ln.strip() else ln
                for ln in new_lines
            )

        self._current = self._current[:m.start()] + new_content + self._current[m.end():]
        self._record(label, 'replace_flexible', 'ok')
        return self

    def insert_before(self, marker: str, content: str, label: str,
                      *, required: bool = True) -> 'FilePatch':
        idx = self._current.find(marker)
        if idx == -1:
            self._record(label, 'insert_before', 'not_found' if required else 'skipped')
            self._errors += 1 if required else 0
            return self
        self._current = self._current[:idx] + content + self._current[idx:]
        self._record(label, 'insert_before', 'ok')
        return self

    def insert_after(self, marker: str, content: str, label: str,
                     *, required: bool = True) -> 'FilePatch':
        idx = self._current.find(marker)
        if idx == -1:
            self._record(label, 'insert_after', 'not_found' if required else 'skipped')
            self._errors += 1 if required else 0
            return self
        end = idx + len(marker)
        self._current = self._current[:end] + content + self._current[end:]
        self._record(label, 'insert_after', 'ok')
        return self

    def assert_contains(self, needle: str, label: str) -> 'FilePatch':
        """Validação pós-patch: o arquivo final contém `needle`?"""
        if needle in self._current:
            self._record(label, 'assert_contains', 'ok')
        else:
            self._record(label, 'assert_contains', 'error', f'"{needle[:40]}..." ausente')
            self._errors += 1
        return self

    def assert_not_contains(self, needle: str, label: str) -> 'FilePatch':
        """Validação pós-patch: o arquivo final NÃO contém `needle`?"""
        if needle not in self._current:
            self._record(label, 'assert_not_contains', 'ok')
        else:
            self._record(label, 'assert_not_contains', 'error', f'"{needle[:40]}..." ainda presente')
            self._errors += 1
        return self

    # ---------------- Finalização ----------------

    def _record(self, label: str, kind: str, status: str, detail: str = '') -> None:
        self._ops.append(Op(label=label, kind=kind, status=status, detail=detail))

    @property
    def has_changes(self) -> bool:
        return self._current != self._original

    @property
    def failed(self) -> bool:
        return self._errors > 0

    def commit(self) -> bool:
        """Imprime relatório e escreve se todas as ops required passaram."""
        self._print_report()

        if self._errors > 0:
            print(RED(f'\n❌ {self._errors} erro(s) — arquivo NÃO foi modificado'))
            return False

        if not self.has_changes:
            print(DIM(f'\nℹ️  Nenhuma alteração efetiva'))
            return True

        if self.dry_run:
            print(YELLOW(f'\n🔍 DRY RUN — arquivo não foi escrito'))
            return True

        self.path.write_text(self._current, encoding='utf-8')
        print(GREEN(f'\n✅ {self.path} atualizado'))
        return True

    def _print_report(self) -> None:
        print()
        print(BLUE(f'📄 {self.path}'))
        print(DIM('─' * 60))
        if not self._ops:
            print(DIM('  (sem operações)'))
            return
        for op in self._ops:
            detail = DIM(f'  ({op.detail})') if op.detail else ''
            print(f'  {op.icon}  {op.label:<45} {detail}')


# ============================================================
# API de conveniência
# ============================================================
def patch(path: str, dry_run: bool = False) -> FilePatch:
    return FilePatch(path, dry_run=dry_run)


def exit_ok(all_results: list[bool]) -> None:
    """Encerra com código 0 se tudo ok, 1 se algo falhou."""
    if all(all_results):
        sys.exit(0)
    sys.exit(1)
