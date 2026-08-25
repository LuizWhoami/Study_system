import markdown
import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Tags HTML permitidas (seguras)
ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'strong', 'em', 'b', 'i', 'u', 'del', 's',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span', 'div',
    'input', 'label',  # para checklists
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'input': ['type', 'checked', 'disabled'],
    'span': ['class'],
    'div': ['class'],
}

@register.filter(name='markdown')
def render_markdown(value):
    if not value:
        return ''
    # Converte Markdown para HTML
    html = markdown.markdown(value, extensions=[
        'extra',           # tabelas, listas, etc.
        'codehilite',      # syntax highlighting (opcional)
        'toc',             # índice
        'nl2br',           # quebras de linha
        'sane_lists',      # listas mais inteligentes
    ])
    # Sanitiza para evitar XSS
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    return mark_safe(clean_html)
