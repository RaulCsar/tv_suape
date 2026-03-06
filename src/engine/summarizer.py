import os
import logging
from google import genai

logger = logging.getLogger(__name__)

class NewsSummarizer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            # Novo SDK oficial do Google
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Módulo summarizer ativado com Gemini (novo SDK).")
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY não definida. O resumo por IA não será executado.")

    def summarize_title(self, text: str) -> str:
        """
        Resume um texto longo para transformá-lo em uma manchete atraente.
        Se houver falha ou falta de API_KEY, retorna um corte simples.
        """
        # Se for muito curto não vale o custo de API
        if len(text) < 100 or not self.client:
            return self._fallback_cut(text)
        
        try:
            prompt = (
                "Atue como um editor de jornalismo para uma TV Corporativa (Digital Signage). "
                "Leia o texto da postagem abaixo e extraia uma manchete curta, direta e informativa "
                "que caiba bem em uma tela de TV (máximo de 15 palavras e menos que 120 caracteres). "
                "Retorne apenas o título final limpo, sem aspas, asteriscos ou explicações:\n\n"
                f"{text}"
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            headline = response.text.strip().replace('"', '').replace('\n', ' ')
            
            # Checagem de segurança pra ver se a API não retornou besteira longa
            if len(headline) > 150:
                return self._fallback_cut(headline)
            
            return headline
        except Exception as e:
            logger.error(f"Erro ao resumir com Google Gemini: {e}")
            return self._fallback_cut(text)
            
    def _fallback_cut(self, text: str) -> str:
        # Fallback de corte manual clássico se não houver Gemini
        return text[:147] + "..." if len(text) > 150 else text