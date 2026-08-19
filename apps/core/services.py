import json
import logging
import re
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY não configurada. Serviço desativado.")
            self.enabled = False
        else:
            self.client = Groq(api_key=self.api_key)
            self.enabled = True

    def gerar_flashcards(self, texto, quantidade=5):
        if not self.enabled:
            return []

        # Validação: texto deve ter pelo menos 20 caracteres
        if not texto or len(texto.strip()) < 20:
            logger.warning(f"Texto muito curto: {texto[:50]}...")
            return []

        prompt = f"""
        Instrução: Gere {quantidade} flashcards (pergunta e resposta) com base no texto fornecido.
        IMPORTANTE:
        - Responda APENAS com um JSON válido.
        - NÃO inclua tags, explicações, "think", ou qualquer texto extra.
        - O JSON deve ser um array de objetos com as chaves "pergunta" e "resposta".
        Exemplo de formato:
        [
            {{"pergunta": "Qual é a capital do Brasil?", "resposta": "Brasília"}},
            {{"pergunta": "Quem descobriu o Brasil?", "resposta": "Pedro Álvares Cabral"}}
        ]
        Texto:
        {texto}
        JSON:
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você é um assistente que responde APENAS com JSON válido. NUNCA inclua tags, explicações ou texto extra."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            conteudo = response.choices[0].message.content.strip()
            logger.info(f"Resposta bruta (primeiros 500 caracteres): {conteudo[:500]}...")

            # ===== LIMPEZA AGRESSIVA =====
            # 1. Remove tags <think>...</think>
            conteudo_limpo = re.sub(r'<think>.*?</think>', '', conteudo, flags=re.DOTALL)

            # 2. Remove qualquer texto antes do primeiro [
            inicio = conteudo_limpo.find('[')
            if inicio != -1:
                conteudo_limpo = conteudo_limpo[inicio:]

            # 3. Remove qualquer texto depois do último ]
            fim = conteudo_limpo.rfind(']')
            if fim != -1:
                conteudo_limpo = conteudo_limpo[:fim+1]

            # 4. Tenta parsear JSON
            try:
                data = json.loads(conteudo_limpo)
                if isinstance(data, list) and len(data) > 0:
                    return data
                else:
                    logger.error(f"JSON não é um array válido: {conteudo_limpo[:200]}")
                    return []
            except json.JSONDecodeError:
                # 5. Tenta encontrar JSON com regex mais flexível
                match = re.search(r'\[\s*\{.*\}\s*\]', conteudo_limpo, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group())
                        if isinstance(data, list):
                            return data
                    except:
                        pass
                logger.error(f"Falha ao parsear JSON. Resposta bruta (primeiros 500 chars): {conteudo[:500]}")
                return []

        except Exception as e:
            logger.error(f"Erro ao gerar flashcards com Groq: {e}")
            return []
