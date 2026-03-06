import logging
import json
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class HTMLRenderer:
    def __init__(self, template_dir: Path, output_file: Path):
        self.template_dir = template_dir
        self.output_file = output_file
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        
    def render(self, news_items: List[Dict[str, Any]]):
        """Renderiza o array de notícias usando Jinja2 no HTML/Reveal.js."""
        try:
            logger.info(f"Renderizando arquivo HTML em {self.output_file} com {len(news_items)} notícias.")
            template = self.env.get_template('index.html.j2')
            
            # Dump das informações (se o template precisar em runtime por JS ou renderização server-side)
            html_content = template.render(
                news_items=news_items,
                news_items_json=json.dumps(news_items)
            )
            
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            self.output_file.write_text(html_content, encoding='utf-8')
            logger.info("Renderização HTML concluída com sucesso.")
        except Exception as e:
            logger.exception(f"Falha ao compilar o template Jinja2: {e}")
