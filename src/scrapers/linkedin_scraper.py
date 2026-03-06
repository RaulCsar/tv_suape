import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from .base import BaseScraper

# Carrega as variáveis de ambiente do .env na raiz do projeto (se existir)
load_dotenv()

logger = logging.getLogger(__name__)

class LinkedInSuapeScraper(BaseScraper):
    def __init__(self, page_url: str = "https://www.linkedin.com/company/complexo-industrial-portu%C3%A1rio-de-suape/"):
        self.page_url = page_url
        self.cookie = os.getenv("LINKEDIN_COOKIE")

    def get_news(self) -> List[Dict[str, Any]]:
        if not self.cookie:
            logger.warning("Variável de ambiente LINKEDIN_COOKIE não definida. Scraper poderá falhar ou exigir login.")
            
        news_list = []
        try:
            logger.info("Iniciando scraper do LinkedIn via Playwright.")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                if self.cookie:
                    context.add_cookies([
                        {
                            "name": "li_at",
                            "value": self.cookie,
                            "domain": ".linkedin.com",
                            "path": "/",
                            "secure": True,
                            "httpOnly": True
                        }
                    ])
                
                page = context.new_page()
                page.set_default_timeout(30000)
                page.goto(self.page_url, wait_until="domcontentloaded")
                
                # Aguarda o feed principal aparecer
                try:
                    page.wait_for_selector(".feed-shared-update-v2", timeout=15000)
                except PlaywrightTimeoutError:
                    logger.error("Tempo limite excedido aguardando o feed do LinkedIn. Tirando screenshot e salvando HTML para debug.")
                    page.screenshot(path="linkedin_debug.png")
                    with open("linkedin_debug.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    logger.error("Verifique linkedin_debug.png e linkedin_debug.html na raiz.")
                    return news_list
                
                posts = page.locator(".feed-shared-update-v2").all()[:5]
                
                for post in posts:
                    try:
                        # Seletores ajustados conforme DOM do LinkedIn. Usamos `.first` para resolver casos de "strict mode violation" onde ele acha múltiplas divs aninhadas
                        text_loc = post.locator(".feed-shared-update-v2__description, .update-components-text").first
                        img_loc = post.locator(".update-components-image__image").first
                        
                        title = text_loc.inner_text().strip() if text_loc.count() > 0 else ""
                        img_url = img_loc.get_attribute("src") if img_loc.count() > 0 else None
                        
                        # Retiramos o encurtamento prematuro aqui! O texto original completo será passado 
                        # para o LLM gerar uma manchete real e inteligente antes da engine.
                        
                        if title and img_url:
                            news_list.append({
                                "title": title,
                                "image_url": img_url,
                                "source": "LinkedIn"
                            })
                    except Exception as e:
                        logger.warning(f"Erro ao processar um post específico do LinkedIn: {e}")
                        continue
                
                browser.close()
                logger.info(f"Coletadas {len(news_list)} do LinkedIn.")
        except Exception as e:
            logger.exception(f"Erro inesperado no scraper do LinkedIn: {e}")
            
        return news_list

if __name__ == "__main__":
    import json
    
    # Configuração de logging apenas para este teste
    logging.basicConfig(level=logging.INFO)
    
    scraper = LinkedInSuapeScraper()
    print("Iniciando testes no scraper do LinkedIn...")
    try:
        resultados = scraper.get_news()
        print(json.dumps(resultados, indent=2, ensure_ascii=False))
        if not resultados:
            print("\nNenhum resultado obtido. Verifique se o selector CSS mudou, se você tomou shadow ban ou se precisa definir a .env com LINKEDIN_COOKIE")
    except Exception as exc:
        print(f"Erro ao testar LinkedIn: {exc}")
