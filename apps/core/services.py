import json
import logging
import re
import random
from django.conf import settings

logger = logging.getLogger(__name__)

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
            logger.warning("IA não retornou questões, usando fallback.")
        return self._extract_questoes(texto, quantidade)

    def _gerar_com_ia(self, texto, quantidade, tipo='flashcard'):
        try:
            import json
            if tipo == 'flashcard':
                prompt = f"""Gere {quantidade} flashcards em JSON puro. Formato: [{{"pergunta":"...","resposta":"..."}}]
                Texto: {texto}"""
                model = "llama3-70b-8192"
                max_tokens = 600
            else:
                prompt = f"""Gere {quantidade} questões de múltipla escolha em JSON puro.
                Cada questão deve ter: enunciado, alternativas (a,b,c,d), correta, explicacao.
                Formato: [{{"enunciado":"...","alternativas":{{"a":"...","b":"...","c":"...","d":"..."}},"correta":"a","explicacao":"..."}}]
                Texto: {texto}"""
                model = "llama3-70b-8192"
                max_tokens = 800

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um assistente que responde APENAS com JSON. NUNCA inclua texto antes ou depois."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens
            )
            conteudo = response.choices[0].message.content.strip()
            logger.info(f"Resposta bruta IA: {conteudo[:200]}...")

            conteudo = re.sub(r'<think>.*?</think>', '', conteudo, flags=re.DOTALL)
            match = re.search(r'\[\s*\{.*\}\s*\]', conteudo, re.DOTALL)
            if match:
                json_str = match.group()
                data = json.loads(json_str)
                if isinstance(data, list) and len(data) > 0:
                    # Embaralha alternativas
                    for item in data:
                        if 'alternativas' in item and 'correta' in item:
                            alt = item['alternativas']
                            correta_original = alt.get(item['correta'], '')
                            keys = list(alt.keys())
                            random.shuffle(keys)
                            novas_alt = {k: alt[k] for k in keys}
                            nova_correta = None
                            for k, v in novas_alt.items():
                                if v == correta_original:
                                    nova_correta = k
                                    break
                            item['alternativas'] = novas_alt
                            item['correta'] = nova_correta if nova_correta else 'a'
                    return data
            return None
        except Exception as e:
            logger.error(f"Erro na IA: {e}")
            return None

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
        while len(flashcards) < quantidade:
            flashcards.append({'pergunta': 'Qual é a ideia central do texto?', 'resposta': texto[:150] if texto else 'Texto não fornecido.'})
        unicos = []
        perguntas_vistas = set()
        for f in flashcards:
            if f['pergunta'] not in perguntas_vistas and f['resposta'] != '...':
                perguntas_vistas.add(f['pergunta'])
                unicos.append(f)
        return unicos[:quantidade]

    def _extract_questoes(self, texto, quantidade):
        """Extrai questões APENAS de frases completas com 'é' ou 'são'."""
        logger.info("Extraindo questões do texto (modo limpo).")
        
        # Limpeza agressiva: remove títulos, listas, markdown
        texto_limpo = re.sub(r'^#.*$', '', texto, flags=re.MULTILINE)
        texto_limpo = re.sub(r'^-.*$', '', texto_limpo, flags=re.MULTILINE)
        texto_limpo = re.sub(r'^>.*$', '', texto_limpo, flags=re.MULTILINE)
        texto_limpo = re.sub(r'\*\*(.*?)\*\*', r'\1', texto_limpo)
        texto_limpo = re.sub(r'\*(.*?)\*', r'\1', texto_limpo)
        texto_limpo = re.sub(r'`(.*?)`', r'\1', texto_limpo)
        texto_limpo = re.sub(r'[“”"\']', '', texto_limpo)
        texto_limpo = re.sub(r'[→▶⇒➔]', '', texto_limpo)
        
        # Divide em frases (ponto final ou interrogação)
        frases = re.split(r'[.!?]\s+', texto_limpo)
        frases = [f.strip() for f in frases if f.strip()]
        
        # Filtra apenas frases com 'é' ou 'são'
        definicoes = []
        for frase in frases:
            if ' é ' in frase or ' são ' in frase:
                # Extrai termo e definição
                if ' é ' in frase:
                    partes = frase.split(' é ', 1)
                else:
                    partes = frase.split(' são ', 1)
                if len(partes) == 2:
                    termo = partes[0].strip()
                    definicao = partes[1].strip()
                    # Filtra: termo curto (<= 5 palavras) e definição longa (> 5 palavras)
                    if len(termo.split()) <= 5 and len(definicao.split()) >= 5:
                        definicoes.append((termo, definicao))
        
        # Se não encontrou, tenta extrair de linhas que contêm 'é' ou 'são'
        if not definicoes:
            linhas = texto_limpo.split('\n')
            for linha in linhas:
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
        
        # Embaralha para variar
        random.shuffle(definicoes)
        selecionadas = definicoes[:quantidade * 2]
        
        questoes = []
        padroes_pergunta = [
            "O que significa \"{termo}\"?",
            "Qual é o significado de \"{termo}\"?",
            "Como se define \"{termo}\"?",
            "O que quer dizer \"{termo}\"?",
            "Qual conceito é descrito por \"{termo}\"?"
        ]
        
        for termo, definicao in selecionadas:
            if len(questoes) >= quantidade:
                break
            padrao = random.choice(padroes_pergunta)
            enunciado = padrao.format(termo=termo)
            
            # Distratores: usa outros termos ou genéricos
            outros = [t for t, d in definicoes if t != termo][:2]
            alternativas = {}
            alternativas['a'] = definicao
            if len(outros) >= 1:
                alternativas['b'] = f'{outros[0]} é um conceito relacionado, mas não é a definição correta.'
            else:
                alternativas['b'] = 'Este termo se refere a um método de estudo.'
            if len(outros) >= 2:
                alternativas['c'] = f'{outros[1]} pode ser confundido com este termo.'
            else:
                alternativas['c'] = 'Outra definição não relacionada.'
            alternativas['d'] = 'Nenhuma das alternativas está correta.'
            
            # Embaralha
            keys = list(alternativas.keys())
            random.shuffle(keys)
            novas_alt = {k: alternativas[k] for k in keys}
            nova_correta = None
            for k, v in novas_alt.items():
                if v == definicao:
                    nova_correta = k
                    break
            
            questoes.append({
                'enunciado': enunciado,
                'alternativas': novas_alt,
                'correta': nova_correta if nova_correta else 'a',
                'explicacao': f'A definição correta é: {definicao[:200]}'
            })
        
        # Se ainda não tem questões, fallback genérico
        while len(questoes) < quantidade:
            questoes.append({
                'enunciado': 'Qual é a ideia central do texto?',
                'alternativas': {
                    'a': texto[:50] if texto else 'Texto não fornecido',
                    'b': 'Texto não fornecido',
                    'c': 'Nenhuma',
                    'd': 'Todas'
                },
                'correta': 'a',
                'explicacao': 'A ideia central é extraída do texto.'
            })
        
        unicos = []
        vistos = set()
        for q in questoes:
            if q['enunciado'] not in vistos:
                vistos.add(q['enunciado'])
                unicos.append(q)
        
        return unicos[:quantidade]
