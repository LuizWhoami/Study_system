import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)

class GroqService:
    """
    Serviço que gera flashcards a partir de um texto.
    Primeiro tenta usar a IA (Groq), se falhar usa extração manual.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.enabled = bool(self.api_key)
        if self.enabled:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except ImportError:
                self.enabled = False
                logger.warning("Groq não instalado. Usando apenas fallback manual.")
        else:
            logger.info("Groq desativado (chave não configurada). Usando fallback manual.")

    def gerar_flashcards(self, texto, quantidade=5):
        """
        Gera flashcards a partir do texto.
        Tenta IA primeiro, se falhar usa extração manual.
        """
        # Tenta usar IA se estiver habilitada
        if self.enabled and texto and len(texto.strip()) >= 20:
            flashcards = self._gerar_com_ia(texto, quantidade)
            if flashcards:
                return flashcards

        # Fallback: extração manual
        return self._extract_flashcards(texto, quantidade)

    def _gerar_com_ia(self, texto, quantidade):
        """Tenta gerar flashcards com a IA Groq."""
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)

            prompt = f"""Gere {quantidade} flashcards em JSON. Exemplo: [{{"pergunta":"...","resposta":"..."}}].
            Texto: {texto}"""

            response = client.chat.completions.create(
                model="",
                messages=[
                    {"role": "system", "content": "Responda APENAS com JSON. Sem tags, sem explicações."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=600
            )
            conteudo = response.choices[0].message.content.strip()
            logger.info(f"Resposta IA: {conteudo[:150]}...")

            # Limpeza
            import re, json
            conteudo = re.sub(r'<think>.*?</think>', '', conteudo, flags=re.DOTALL)
            match = re.search(r'\[\s*\{.*\}\s*\]', conteudo, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if isinstance(data, list) and len(data) > 0:
                    # Valida e limpa placeholders
                    for flash in data:
                        if not flash.get('pergunta', '').strip() or flash['pergunta'] == '...':
                            flash['pergunta'] = 'Pergunta não disponível'
                        if not flash.get('resposta', '').strip() or flash['resposta'] == '...':
                            flash['resposta'] = 'Resposta não disponível'
                    return data
        except Exception as e:
            logger.error(f"Erro na IA: {e}")
        return None

    def _extract_flashcards(self, texto, quantidade):
        """Extrai flashcards diretamente do texto (fallback)."""
        logger.info("Extraindo flashcards manualmente do texto.")
        linhas = texto.split('\n')
        flashcards = []
        titulo_atual = None

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Captura títulos (#, ##, etc.)
            if linha.startswith('#'):
                titulo = re.sub(r'^#+\s*', '', linha)
                if titulo and len(titulo) > 2:
                    titulo_atual = titulo
                    flashcards.append({
                        'pergunta': f'Qual é o tema "{titulo[:40]}"?',
                        'resposta': titulo
                    })
                continue

            # Captura itens de lista
            if linha.startswith('-') or linha.startswith('*'):
                item = re.sub(r'^[-*]\s*', '', linha)
                if item and len(item) > 3:
                    if titulo_atual:
                        flashcards.append({
                            'pergunta': f'O que é "{item[:40]}"?',
                            'resposta': f'{item} (mencionado em {titulo_atual})'
                        })
                    else:
                        flashcards.append({
                            'pergunta': f'O que significa "{item[:40]}"?',
                            'resposta': item
                        })
                continue

            # Captura frases com conteúdo relevante (≥ 10 palavras)
            if len(linha.split()) >= 8:
                frase = linha[:120]
                flashcards.append({
                    'pergunta': f'Qual informação importante sobre "{frase[:30]}..."?',
                    'resposta': frase
                })

            if len(flashcards) >= quantidade * 2:
                break

        # Se não encontrou nada, cria flashcards genéricos
        if not flashcards:
            palavras = texto.split()[:80]
            if palavras:
                resumo = ' '.join(palavras)
                flashcards = [
                    {'pergunta': 'Qual é o tema principal do texto?', 'resposta': resumo[:200]},
                    {'pergunta': 'Cite uma ideia central do texto.', 'resposta': ' '.join(palavras[10:30])},
                ]

        # Remove duplicatas (mantém apenas perguntas únicas)
        unicos = []
        perguntas_vistas = set()
        for f in flashcards:
            pergunta = f['pergunta']
            if pergunta not in perguntas_vistas:
                perguntas_vistas.add(pergunta)
                unicos.append(f)

        # Garante que temos exatamente 'quantidade' flashcards
        while len(unicos) < quantidade:
            if texto:
                unicos.append({
                    'pergunta': f'Qual é a ideia principal do texto?',
                    'resposta': texto[:100] if texto else 'Texto não fornecido.'
                })
            else:
                unicos.append({
                    'pergunta': 'Nenhum conteúdo disponível',
                    'resposta': 'Adicione conteúdo à nota para gerar flashcards.'
                })

        return unicos[:quantidade]
