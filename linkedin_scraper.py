import json
import logging
import os
from typing import Dict, List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from .base import Scraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LinkedInSuapeScraper(Scraper):
    """
    Scraper para extrair posts da página do LinkedIn do Porto de Suape usando Playwright.
    Requer um cookie de autenticação para evitar bloqueios.
    """

    def __init__(self, profile_url: str = "https://www.linkedin.com/company/complexo-industrial-portu%C3%A1rio-de-suape/posts"):
        self.profile_url = profile_url
        self.linkedin_cookie = os.getenv("LINKEDIN_COOKIE")

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

                # Aguarda os posts carregarem
                page.wait_for_selector("div.update-components-actor__title", timeout=30000)

                posts = page.locator("div.feed-shared-update-v2").all()
                if not posts:
                    logging.warning("Nenhum post encontrado no LinkedIn. A estrutura pode ter mudado.")
                    return []

                for post in posts[:5]:  # Limita aos 5 posts mais recentes
                    try:
                        headline_element = post.locator("div.feed-shared-update-v2__description-wrapper").first
                        headline = headline_element.inner_text(timeout=5000).strip()

                        image_element = post.locator("img.update-components-image__image").first
                        image_url = image_element.get_attribute("src")

                        if headline and image_url:
                            news_list.append({"headline": headline, "image_url": image_url})
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