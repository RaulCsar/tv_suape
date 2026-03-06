import logging
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)

class SiteSuapeScraper(BaseScraper):
    def __init__(self, url: str = "https://www.suape.pe.gov.br/", timeout: int = 15):
        self.url = url
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_news(self) -> List[Dict[str, Any]]:
        news_list = []
        try:
            logger.info(f"Iniciando raspagem do Site Oficial: {self.url}")
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Buscando na página inicial (onde ficam os destaques com imagens)
            articles = soup.find_all("div", class_="media")[:5]
            
            for article in articles:
                # O título fica dentro de um <h4 class="title"> -> <a>
                title_tag = article.find("h4", class_="title")
                if not title_tag:
                    continue
                
                a_tag = title_tag.find("a")
                title = a_tag.get_text(strip=True) if a_tag else title_tag.get_text(strip=True)
                
                # A imagem usa a classe "imagens-not-home"
                img_tag = article.find("img", class_="imagens-not-home")
                
                if title and img_tag:
                    img_url = img_tag.get("src")
                    if img_url and not img_url.startswith("http"):
                        img_url = "https://www.suape.pe.gov.br" + img_url
                        
                    news_list.append({
                        "title": title,
                        "image_url": img_url,
                        "source": "Site Oficial"
                    })
            logger.info(f"Coletadas {len(news_list)} notícias do Site Oficial.")
        except requests.Timeout:
            logger.error("Timeout ao tentar acessar o Site Oficial de Suape.")
        except requests.RequestException as e:
            logger.error(f"Erro de requisição ao acessar Site Oficial: {e}")
        except Exception as e:
            logger.exception(f"Erro inesperado no scraper do Site Oficial: {e}")
            
        return news_list
