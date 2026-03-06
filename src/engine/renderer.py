import logging
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class StaticSiteRenderer:
    """
    Renderiza o site estático (index.html) usando Jinja2 e uma lista de imagens.
    """

    def __init__(self, template_dir: Path, template_name: str, output_path: Path):
        self.output_path = output_path
        try:
            self.env = Environment(loader=FileSystemLoader(str(template_dir.absolute())))
            self.template = self.env.get_template(template_name)
        except TemplateNotFound:
            logging.error(f"Template '{template_name}' não encontrado em '{template_dir}'.")
            raise
        except Exception as e:
            logging.error(f"Erro ao inicializar o Jinja2 Environment: {e}")
            raise

    def render(self, image_paths: List[Path], slide_duration_ms: int = 10000) -> bool:
        """
        Gera o arquivo HTML final a partir do template e da lista de imagens.
        """
        # Converte os caminhos absolutos para relativos ao arquivo HTML de saída
        relative_image_paths = []
        html_parent_dir = self.output_path.parent
        for img_path in image_paths:
            try:
                relative_path = img_path.relative_to(html_parent_dir)
                relative_image_paths.append(relative_path.as_posix())  # Garante barras '/'
            except ValueError:
                logging.warning(f"Não foi possível criar caminho relativo para {img_path}")

        context = {
            "images": sorted(relative_image_paths),
            "slide_duration_ms": slide_duration_ms,
        }

        try:
            html_content = self.template.render(context)
            self.output_path.write_text(html_content, encoding="utf-8")
            logging.info(f"Site estático renderizado com sucesso em: {self.output_path}")
            return True
        except Exception as e:
            logging.error(f"Falha ao renderizar ou salvar o template HTML: {e}", exc_info=True)
            return False