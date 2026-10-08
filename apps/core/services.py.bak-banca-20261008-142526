"""
Serviços compartilhados do LSStudy.

`GroqService` encapsula a integração com a API do Groq para:
  - geração de flashcards (usado por `notes`)
  - geração de questões (usado por `notes` e `questions`)

Se a API falhar, o serviço cai num fallback manual que extrai
conteúdo do texto via regex. Para questões, o fallback NÃO inventa
perguntas genéricas — devolve lista vazia para o caller tratar.
"""
import json
import logging
import re
import random

from django.conf import settings

logger = logging.getLogger(__name__)

MODEL = "openai/gpt-oss-120b"


class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.enabled = bool(self.api_key)
        if self.enabled:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq inicializado com sucesso.")
            except ImportError:
                self.enabled = False
                logger.warning("Groq não instalado.")
            except Exception as e:
                self.enabled = False
                logger.error(f"Erro ao inicializar Groq: {e}")
        else:
            logger.warning("GROQ_API_KEY não configurada. Usando apenas fallback manual.")

    # ==========================================================
    # API PÚBLICA
    # ==========================================================
    def gerar_flashcards(self, texto, quantidade=5):
        if self.enabled and texto and len(texto.strip()) >= 20:
            flashcards = self._gerar_com_ia(texto, quantidade, tipo='flashcard')
            if flashcards:
                return flashcards
            logger.warning("IA não retornou flashcards, usando fallback.")
        return self._extract_flashcards(texto, quantidade)

    def gerar_questoes(self, texto, quantidade=3):
        if self.enabled and texto and len(texto.strip()) >= 20:
            questoes = self._gerar_com_ia(texto, quantidade, tipo='questao')
            if questoes:
                return questoes
            logger.warning("IA não retornou questões, usando fallback manual.")
        return self._extract_questoes(texto, quantidade)

    # ==========================================================
    # CHAMADA À IA
    # ==========================================================
    def _gerar_com_ia(self, texto, quantidade, tipo='flashcard'):
        try:
            if tipo == 'flashcard':
                prompt = self._prompt_flashcards(texto, quantidade)
                max_tokens = 800
            else:
                prompt = self._prompt_questoes(texto, quantidade)
                max_tokens = 2000

            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você responde APENAS com JSON válido. "
                            "NUNCA inclua texto antes ou depois. "
                            "NUNCA use markdown, blocos ```json, ou comentários."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=max_tokens,
            )
            conteudo = response.choices[0].message.content.strip()
            logger.info("Resposta bruta IA (primeiros 200 chars): %s", conteudo[:200])

            conteudo = re.sub(r'<think>.*?</think>', '', conteudo, flags=re.DOTALL)
            conteudo = re.sub(r'^```(?:json)?\s*', '', conteudo)
            conteudo = re.sub(r'\s*```$', '', conteudo)

            match = re.search(r'\[\s*\{.*\}\s*\]', conteudo, re.DOTALL)
            if not match:
                logger.warning("IA não retornou JSON array válido.")
                return None

            data = json.loads(match.group())
            if not isinstance(data, list) or not data:
                return None

            if tipo == 'questao':
                data = [self._normalizar_questao(q) for q in data if isinstance(q, dict)]
                data = [q for q in data if q is not None]
                return data if data else None

            return data

        except json.JSONDecodeError as e:
            logger.error("JSON inválido da IA: %s", e)
            return None
        except Exception as e:
            logger.error("Erro na IA: %s", e)
            return None

    # ==========================================================
    # PROMPTS
    # ==========================================================
    def _prompt_flashcards(self, texto, quantidade):
        return f"""Você é um professor especialista em concursos públicos brasileiros.
Gere {quantidade} flashcards de estudo sobre o TEMA abaixo.

TEMA:
{texto}

REGRAS:
- Cada flashcard tem uma pergunta objetiva e uma resposta concisa.
- Foque em conceitos que realmente caem em prova.
- Varie: definições, aplicações, comparações, fórmulas.

FORMATO — APENAS JSON puro:
[
  {{"pergunta": "texto", "resposta": "texto"}}
]"""

    def _prompt_questoes(self, texto, quantidade):
        return f"""Você é um professor especialista em concursos públicos brasileiros.
Gere EXATAMENTE {quantidade} questões de múltipla escolha, nível médio, sobre o TEMA abaixo.

TEMA:
{texto}

REGRAS OBRIGATÓRIAS:
1. Cada questão tem 4 alternativas (a, b, c, d) — apenas UMA correta.
2. Os distratores devem ser PLAUSÍVEIS: erros comuns, conceitos parecidos, exceções mal aplicadas.
   NUNCA use "Nenhuma das alternativas" ou "Todas as anteriores".
3. Varie os tipos de cobrança: definição, aplicação prática, comparação entre conceitos,
   identificação de erro, situação-problema.
4. A explicação deve ter 2 partes: por que a correta está certa E por que os distratores estão errados.
   IMPORTANTE: NÃO mencione letras (a, b, c, d) na explicação. Em vez de
   "a alternativa (c) está correta", escreva "a alternativa que menciona a mesma
   chave secreta está correta". Isso é obrigatório porque o sistema embaralha
   as alternativas depois.
5. NÃO gere questões meta como "Qual é a ideia central do texto?".
6. NÃO repita o mesmo assunto em duas questões.
7. Se o TEMA for apenas um nome (ex: "PF > Informática > Criptografia"),
   use seu CONHECIMENTO PRÓPRIO sobre o assunto — invente questões reais e cobráveis.
8. Se o TEMA contiver texto longo, baseie-se NELE, mas não copie literalmente.

FORMATO DE SAÍDA — APENAS JSON puro, sem markdown:
[
  {{
    "enunciado": "texto completo da questão",
    "alternativas": {{"a": "...", "b": "...", "c": "...", "d": "..."}},
    "correta": "a",
    "explicacao": "Explicação completa."
  }}
]"""

    # ==========================================================
    # NORMALIZAÇÃO / EMBARALHAMENTO
    # ==========================================================
    def _normalizar_questao(self, q):
        """Valida e embaralha uma questão. Devolve None se inválida."""
        if not isinstance(q, dict):
            return None

        enunciado = (q.get('enunciado') or '').strip()
        if not enunciado:
            return None

        alt = q.get('alternativas')
        if not isinstance(alt, dict):
            return None

        letras = ['a', 'b', 'c', 'd']
        for l in letras:
            if not (alt.get(l) or '').strip():
                return None

        correta = (q.get('correta') or '').strip().lower()
        if correta not in letras:
            return None

        # Descobre o texto da correta antes de embaralhar
        texto_correta = alt[correta]

        # Embaralha mantendo o mapeamento
        itens = [(k, v) for k, v in alt.items()]
        random.shuffle(itens)
        novas_alt = {letras[i]: v for i, (_, v) in enumerate(itens)}

        nova_correta = None
        for k, v in novas_alt.items():
            if v == texto_correta:
                nova_correta = k
                break

        return {
            'enunciado': enunciado,
            'alternativas': novas_alt,
            'correta': nova_correta or 'a',
            'explicacao': (q.get('explicacao') or '').strip(),
        }

    # ==========================================================
    # FALLBACK MANUAL — flashcards
    # ==========================================================
    def _extract_flashcards(self, texto, quantidade):
        logger.info("Extraindo flashcards manualmente.")
        linhas = texto.split('\n')
        flashcards = []
        definicoes = []
        topicos = {}
        titulo_atual = None
        conteudo_atual = []

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            if linha.startswith('#'):
                if titulo_atual and conteudo_atual:
                    topicos[titulo_atual] = '\n'.join(conteudo_atual)
                titulo = re.sub(r'^#+\s*', '', linha)
                titulo_sem_num = re.sub(r'^[\d\.]+\s*', '', titulo)
                titulo_atual = titulo_sem_num
                conteudo_atual = []
            else:
                if titulo_atual:
                    conteudo_atual.append(linha)
                if ' é ' in linha or ' são ' in linha:
                    partes = re.split(r' (é|são) ', linha, 1)
                    if len(partes) == 3:
                        termo = re.sub(r'^[\d\.]+\s*', '', partes[0].strip())
                        definicao = partes[2].strip()
                        if len(termo) > 3 and len(definicao) > 5:
                            definicoes.append((termo, definicao))

        if titulo_atual and conteudo_atual:
            topicos[titulo_atual] = '\n'.join(conteudo_atual)

        for termo, definicao in definicoes:
            flashcards.append({'pergunta': f'O que significa "{termo}"?', 'resposta': definicao})

        for titulo, conteudo in topicos.items():
            if len(flashcards) >= quantidade:
                break
            definicao_relacionada = None
            for termo, definicao in definicoes:
                if termo.lower() in titulo.lower() or titulo.lower() in termo.lower():
                    definicao_relacionada = definicao
                    break
            if definicao_relacionada:
                flashcards.append({'pergunta': f'O que é "{titulo}"?', 'resposta': definicao_relacionada})
            elif conteudo and len(conteudo) > 20:
                flashcards.append({'pergunta': f'Explique o conceito de "{titulo}".', 'resposta': conteudo[:300]})

        if len(flashcards) < quantidade:
            for linha in linhas:
                if len(flashcards) >= quantidade:
                    break
                linha = linha.strip()
                if ' é ' in linha and len(linha) > 20:
                    termo = linha.split(' é ')[0]
                    termo = re.sub(r'^[\d\.]+\s*', '', termo.strip())
                    if len(termo) > 3:
                        flashcards.append({'pergunta': f'O que é "{termo}"?', 'resposta': linha})

        unicos = []
        perguntas_vistas = set()
        for f in flashcards:
            if f['pergunta'] not in perguntas_vistas and f['resposta'] != '...':
                perguntas_vistas.add(f['pergunta'])
                unicos.append(f)

        return unicos[:quantidade]

    # ==========================================================
    # FALLBACK MANUAL — questões
    # ==========================================================
    def _extract_questoes(self, texto, quantidade):
        """
        Extrai questões APENAS de frases completas com 'é' ou 'são'.
        Não inventa perguntas genéricas — se não encontrar, devolve o que tiver.
        """
        logger.info("Extraindo questões do texto (modo manual).")

        texto_limpo = re.sub(r'^#.*$', '', texto, flags=re.MULTILINE)
        texto_limpo = re.sub(r'^-.*$', '', texto_limpo, flags=re.MULTILINE)
        texto_limpo = re.sub(r'^>.*$', '', texto_limpo, flags=re.MULTILINE)
        texto_limpo = re.sub(r'\*\*(.*?)\*\*', r'\1', texto_limpo)
        texto_limpo = re.sub(r'\*(.*?)\*', r'\1', texto_limpo)
        texto_limpo = re.sub(r'`(.*?)`', r'\1', texto_limpo)
        texto_limpo = re.sub(r'[“”"\']', '', texto_limpo)
        texto_limpo = re.sub(r'[→▶⇒➔]', '', texto_limpo)

        frases = re.split(r'[.!?]\s+', texto_limpo)
        frases = [f.strip() for f in frases if f.strip()]

        definicoes = []
        for frase in frases:
            if ' é ' in frase or ' são ' in frase:
                if ' é ' in frase:
                    partes = frase.split(' é ', 1)
                else:
                    partes = frase.split(' são ', 1)
                if len(partes) == 2:
                    termo = partes[0].strip()
                    definicao = partes[1].strip()
                    if len(termo.split()) <= 5 and len(definicao.split()) >= 5:
                        definicoes.append((termo, definicao))

        if not definicoes:
            for linha in texto_limpo.split('\n'):
                linha = linha.strip()
                if not linha:
                    continue
                if ' é ' in linha or ' são ' in linha:
                    if ' é ' in linha:
                        partes = linha.split(' é ', 1)
                    else:
                        partes = linha.split(' são ', 1)
                    if len(partes) == 2:
                        termo = partes[0].strip()
                        definicao = partes[1].strip()
                        if len(termo.split()) <= 5 and len(definicao.split()) >= 5:
                            definicoes.append((termo, definicao))

        random.shuffle(definicoes)
        selecionadas = definicoes[:quantidade]

        padroes_pergunta = [
            'O que significa "{termo}"?',
            'Qual é o significado de "{termo}"?',
            'Como se define "{termo}"?',
            'O que quer dizer "{termo}"?',
            'Qual conceito é descrito por "{termo}"?',
        ]

        questoes = []
        for termo, definicao in selecionadas:
            padrao = random.choice(padroes_pergunta)
            enunciado = padrao.format(termo=termo)

            outros = [t for t, _ in definicoes if t != termo][:2]
            alternativas = {'a': definicao}
            if len(outros) >= 1:
                alternativas['b'] = f'{outros[0]} é um conceito relacionado, mas não é a definição correta.'
            else:
                alternativas['b'] = 'Este termo se refere a um método de estudo.'
            if len(outros) >= 2:
                alternativas['c'] = f'{outros[1]} pode ser confundido com este termo.'
            else:
                alternativas['c'] = 'Outra definição não relacionada.'
            alternativas['d'] = 'Nenhuma das alternativas está correta.'

            keys = list(alternativas.keys())
            random.shuffle(keys)
            novas_alt = {k: alternativas[k] for k in keys}
            nova_correta = next((k for k, v in novas_alt.items() if v == definicao), 'a')

            questoes.append({
                'enunciado': enunciado,
                'alternativas': novas_alt,
                'correta': nova_correta,
                'explicacao': f'A definição correta é: {definicao[:200]}',
            })

        unicos = []
        vistos = set()
        for q in questoes:
            if q['enunciado'] not in vistos:
                vistos.add(q['enunciado'])
                unicos.append(q)

        return unicos[:quantidade]
