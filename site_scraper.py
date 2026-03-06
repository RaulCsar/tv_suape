import logging
from typing import Dict, List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .base import Scraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SiteSuapeScraper(Scraper):
    """
    Scraper para extrair notícias do site institucional do Porto de Suape.
    Atua como fallback caso o scraper principal (LinkedIn) falhe.
    """

    def __init__(self, base_url: str = "https://www.suape.pe.gov.br"):
        self.base_url = base_url
        self.news_url = urljoin(self.base_url, "/pt/")

    def get_news(self) -> List[Dict[str, str]]:
        """
        Realiza o web scraping da página de notícias, extraindo manchete e URL da imagem.
        """
        logging.info(f"Iniciando scraping do site: {self.news_url}")
        news_list = []
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                response = client.get(self.news_url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('article', class_='suape-card')

                if not cards:
                    logging.warning("Nenhum card de notícia encontrado no site. A estrutura pode ter mudado.")
                    return []

                for card in cards:
                    title_tag = card.find('h4', class_='title')
                    img_tag = card.find('img', class_='imagens-not-home')

                    if title_tag and title_tag.a and img_tag and img_tag.get('src'):
                        headline = title_tag.a.get_text(strip=True)
                        image_url = urljoin(self.base_url, img_tag['src'])
                        news_list.append({"headline": headline, "image_url": image_url})

        except httpx.TimeoutException:
            logging.error("Timeout ao tentar acessar o site de Suape.")
        except httpx.RequestError as e:
            logging.error(f"Erro de requisição ao acessar o site de Suape: {e}")
        except Exception as e:
            logging.error(f"Erro inesperado no scraper do site: {e}", exc_info=True)

        logging.info(f"Scraper do site encontrou {len(news_list)} notícias.")
        return news_list