import logging
import shutil
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from engine.processor import ImageProcessor
from engine.renderer import StaticSiteRenderer
from scrapers.base import Scraper
from scrapers.linkedin_scraper import LinkedInSuapeScraper
from scrapers.site_scraper import SiteSuapeScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Pipeline:
    """Orquestra o pipeline completo: extração, processamento e renderização."""

    def __init__(self, scrapers: List[Scraper], processor: ImageProcessor, renderer: StaticSiteRenderer):
        self.scrapers = scrapers
        self.processor = processor
        self.renderer = renderer

    def _fetch_news(self) -> List[Dict[str, str]]:
        """Busca notícias de todos os scrapers e unifica os resultados."""
        all_news = []
        for scraper in self.scrapers:
            try:
                news = scraper.get_news()
                all_news.extend(news)
            except Exception as e:
                logging.error(f"Falha ao executar scraper {type(scraper).__name__}: {e}", exc_info=True)

        # Remove duplicatas baseadas na URL da imagem, mantendo a primeira ocorrência
        unique_news = []
        seen_urls = set()
        for item in all_news:
            if item["image_url"] not in seen_urls:
                unique_news.append(item)
                seen_urls.add(item["image_url"])

        logging.info(f"Total de {len(unique_news)} notícias únicas encontradas.")
        return unique_news

    def _purge_cache(self, directory: Path):
        """Limpa o diretório de cache (imagens antigas)."""
        logging.info(f"Limpando cache de imagens em: {directory}")
        if directory.exists():
            for item in directory.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

    def run(self):
        """Executa o pipeline completo."""
        logging.info("Iniciando pipeline da TV Suape.")

        # 1. Limpeza do cache
        self._purge_cache(self.processor.output_dir)

        # 2. Extração de dados
        news_items = self._fetch_news()
        if not news_items:
            logging.warning("Nenhuma notícia foi encontrada. O pipeline será encerrado.")
            return

        # 3. Processamento de imagens
        processed_images = []
        for i, item in enumerate(news_items):
            # Gera um nome de arquivo simples e único
            output_filename = f"news_{i:02d}"
            processed_path = self.processor.process_image(item["image_url"], item["headline"], output_filename)
            if processed_path:
                processed_images.append(processed_path)

        # 4. Renderização do site estático
        if processed_images:
            self.renderer.render(image_paths=processed_images)
        else:
            logging.warning("Nenhuma imagem foi processada. O site estático não será gerado.")

        logging.info("Pipeline da TV Suape finalizado.")


if __name__ == "__main__":
    load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

    # Configuração das dependências (Injeção de Dependência)
    ROOT_DIR = Path(__file__).parent.parent
    ASSETS_DIR = ROOT_DIR / "assets"

    scrapers_to_run = [LinkedInSuapeScraper(), SiteSuapeScraper()]
    image_processor = ImageProcessor(output_dir=ASSETS_DIR / "news", font_path=ASSETS_DIR / "fonts/Roboto-Bold.ttf")
    site_renderer = StaticSiteRenderer(template_dir=ROOT_DIR / "templates", template_name="index.html.j2", output_path=ROOT_DIR / "index.html")

    pipeline = Pipeline(scrapers=scrapers_to_run, processor=image_processor, renderer=site_renderer)
    pipeline.run()