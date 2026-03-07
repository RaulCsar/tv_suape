import json
import logging
import os
from typing import Dict, List

from google import genai
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from .base import Scraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LinkedInSuapeScraper(Scraper):
    """
    Scraper para extrair posts da página do LinkedIn do Porto de Suape usando Playwright.
    Requer um cookie de autenticação para evitar bloqueios.
    """

    def __init__(self, profile_url: str = "https://www.linkedin.com/company/complexo-industrial-portu%C3%A1rio-de-suape/posts/?feedView=images"):
        self.profile_url = profile_url
        self.linkedin_cookie = os.getenv("LINKEDIN_COOKIE")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            self.genai_client = genai.Client(api_key=self.gemini_api_key)
        else:
            self.genai_client = None

    def _summarize_with_gemini(self, text: str) -> str:
        """Usa a API do Gemini para resumir a notícia em uma única frase (manchete)."""
        if not self.genai_client:
            return text
        try:
            prompt = f"Resuma o seguinte texto de uma postagem do LinkedIn em uma única frase de impacto curta (máximo 15 palavras), como uma manchete de TV (em português). Remova aspas e quebras de linha: {text}"
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            if response.text:
                return response.text.strip().replace('"', '').replace('\n', ' ')
            return text
        except Exception as e:
            logging.error(f"Erro ao usar Gemini API: {e}")
            return text

    def get_news(self) -> List[Dict[str, str]]:
        """
        Acessa a página de posts, injeta o cookie e extrai as notícias mais recentes.
        """
        if not self.linkedin_cookie:
            logging.warning("Variável de ambiente LINKEDIN_COOKIE não definida. Pulando scraper do LinkedIn.")
            return []

        logging.info(f"Iniciando scraping do LinkedIn: {self.profile_url}")
        news_list = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()

                # Injeta o cookie de sessão
                cookie = {
                    "name": "li_at",
                    "value": self.linkedin_cookie,
                    "domain": ".linkedin.com",
                    "path": "/",
                }
                context.add_cookies([cookie])

                page = context.new_page()
                page.goto(self.profile_url, wait_until="domcontentloaded", timeout=60000)

                # scroll 3 vezes para carregar os posts
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 1000)")
                    page.wait_for_timeout(2000)

                posts = page.locator("div.feed-shared-update-v2").all()
                if not posts:
                    logging.warning("Nenhum post encontrado no LinkedIn. A estrutura pode ter mudado.")
                    return []

                for idx, post in enumerate(posts[:5]):  # Limita aos 5 posts mais recentes
                    try:
                        # Busca o texto na nova estrutura do LinkedIn
                        headline_element = post.locator(".update-components-text, .update-components-update-v2__commentary")
                        if headline_element.count() > 0:
                            headline = headline_element.first.inner_text(timeout=5000).strip()
                        else:
                            headline = ""

                        # Busca todas as imagens e extrai a primeira que seja conteúdo do post
                        image_url = ""
                        imgs = post.locator("img").all()
                        for img in imgs:
                            src = img.get_attribute("src")
                            if src and "company-logo" not in src and "emoji" not in src and "dms/image" in src:
                                image_url = src
                                break

                        if headline and image_url:
                            headline_summary = self._summarize_with_gemini(headline)
                            news_list.append({"headline": headline_summary, "image_url": image_url})
                    except PlaywrightTimeoutError:
                        logging.warning("Timeout ao extrair dados de um post individual do LinkedIn. Pulando.")
                        continue

                browser.close()
        except PlaywrightTimeoutError:
            logging.error("Timeout geral ao carregar a página do LinkedIn. Verifique a conexão ou o seletor.")
        except Exception as e:
            logging.error(f"Erro inesperado no scraper do LinkedIn: {e}", exc_info=True)

        logging.info(f"Scraper do LinkedIn encontrou {len(news_list)} notícias.")
        return news_list