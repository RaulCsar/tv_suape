import logging
import sys
import shutil
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Carrega ambiente
load_dotenv()

from src.scrapers.site_scraper import SiteSuapeScraper
from src.scrapers.linkedin_scraper import LinkedInSuapeScraper
from src.engine.processor import ImageProcessor
from src.engine.renderer import HTMLRenderer
from src.engine.summarizer import NewsSummarizer

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Diretórios baseados no Local do Script
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "news"
TEMPLATES_DIR = BASE_DIR / "templates"
PUBLIC_DIR = BASE_DIR / "public"

def pre_clear_cache(directory: Path):
    """Eficiência: Purge do cache de imagens antigas."""
    logger.info(f"Limpando diretório do cache em {directory}")
    if directory.exists():
        for file in directory.iterdir():
            if file.is_file():
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Erro ao deletar o arquivo {file}: {e}")
    else:
        directory.mkdir(parents=True, exist_ok=True)

def deduplicate_news(news_list: List[Dict]) -> List[Dict]:
    """Remove conteúdo com títulos duplicados antes do processamento."""
    seen_titles = set()
    unique = []
    for item in news_list:
        norm_title = item['title'].strip().lower()
        if norm_title not in seen_titles:
            unique.append(item)
            seen_titles.add(norm_title)
    return unique

def main():
    logger.info("=== Iniciando Pipeline do TV Suape ===")
    
    # 1. Limpeza do Cache
    pre_clear_cache(ASSETS_DIR)
    
    # 2. Execução dos Scrapers (Camada de Extração)
    scrapers = [
        SiteSuapeScraper(),
        LinkedInSuapeScraper()
    ]
    
    all_news = []
    for scraper in scrapers:
        try:
            news = scraper.get_news()
            all_news.extend(news)
        except Exception as e:
            logger.error(f"Scraper falhou: {e}")
            
    # Remove duplicates
    unique_news = deduplicate_news(all_news)
    
    # Ordenação das notícias: Site Oficial primeiro, depois LinkedIn
    unique_news.sort(key=lambda x: 0 if x.get('source') == 'Site Oficial' else 1)
    
    logger.info(f"Total de notícias unificadas e deduplicadas: {len(unique_news)}")
    # 2.5 Resumo por IA das Manchetes
    summarizer = NewsSummarizer()
    for news in unique_news:
        if len(news['title']) > 100:
            logger.info(f"Resumindo texto longo da fonte {news['source']}...")
            news['title'] = summarizer.summarize_title(news['title'])
    
    # 
    # 3. Processamento de Imagem (Camada Pillow)
    processor = ImageProcessor(output_dir=ASSETS_DIR)
    processed_news_list = []
    
    index = 1
    for news in unique_news:
        # Se retornar arquivo processado válido, armazena no array que vai pro template
        filename = processor.process_news_item(news, index)
        if filename:
            news_copy = news.copy()
            news_copy['local_image_name'] = filename
            processed_news_list.append(news_copy)
            index += 1
            
    # Copia as imagens processadas para pasta pública apenas pro Vercel renderizar, 
    # ou os acessa via caminho relativo
    pub_assets = PUBLIC_DIR / "assets" / "news"
    pre_clear_cache(pub_assets)
    shutil.copytree(ASSETS_DIR, pub_assets, dirs_exist_ok=True)
            
    # 4. Renderização (Camada HTML/Jinja2)
    renderer = HTMLRenderer(
        template_dir=TEMPLATES_DIR,
        output_file=PUBLIC_DIR / "index.html"
    )
    renderer.render(processed_news_list)
    
    logger.info("=== Pipeline concluída com sucesso ===")

if __name__ == "__main__":
    main()
