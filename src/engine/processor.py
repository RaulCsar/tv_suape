import logging
import textwrap
from pathlib import Path
from io import BytesIO

import httpx
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ImageProcessor:
    """
    Responsável por processar uma imagem: baixar, redimensionar, aplicar
    efeitos e renderizar texto sobre ela.
    """

    def __init__(self, output_dir: Path, font_path: Path | None = None, tv_width: int = 1920, tv_height: int = 1080):
        self.output_dir = output_dir
        self.tv_width = tv_width
        self.tv_height = tv_height
        self.font_path = font_path
        self.font_size = 60
        self.font = self._load_font()

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Carrega a fonte TrueType, com fallback para uma fonte padrão."""
        if self.font_path:
            try:
                return ImageFont.truetype(str(self.font_path), self.font_size)
            except IOError:
                logging.warning(f"Fonte '{self.font_path}' não encontrada. Usando fonte padrão da Pillow.")
        else:
            logging.info("Nenhum caminho de fonte especificado. Usando fonte padrão da Pillow.")
        return ImageFont.load_default()

    def process_image(self, image_url: str, headline: str, output_filename: str) -> Path | None:
        """
        Orquestra o download e processamento completo de uma imagem.
        Retorna o caminho do arquivo salvo ou None em caso de falha.
        """
        try:
            with httpx.stream("GET", image_url, timeout=20.0, follow_redirects=True) as response:
                response.raise_for_status()
                image_data = response.read()

            with Image.open(BytesIO(image_data)).convert("RGBA") as img:
                # 1. Redimensionar e Recortar (Crop) para 16:9
                target_ratio = self.tv_width / self.tv_height
                img_ratio = img.width / img.height

                if img_ratio > target_ratio:
                    new_width = int(target_ratio * img.height)
                    offset = (img.width - new_width) // 2
                    img = img.crop((offset, 0, img.width - offset, img.height))
                elif img_ratio < target_ratio:
                    new_height = int(img.width / target_ratio)
                    offset = (img.height - new_height) // 2
                    img = img.crop((0, offset, img.width, img.height - offset))

                img = img.resize((self.tv_width, self.tv_height), Image.Resampling.LANCZOS)

                # 2. Aplicar gradiente escuro na base
                gradient = Image.new('L', (1, self.tv_height), color=0xFF)
                for y in range(self.tv_height):
                    gradient.putpixel((0, y), int(255 * (1 - max(0, (y - self.tv_height * 0.6)) / (self.tv_height * 0.4))))
                alpha = gradient.resize(img.size)
                black_bg = Image.new('RGBA', img.size, color=(0, 0, 0, 255))
                img = Image.composite(img, black_bg, alpha)

                # 3. Renderizar texto
                draw = ImageDraw.Draw(img)
                wrapped_text = textwrap.wrap(headline, width=55)

                # Cálculo da posição do texto
                line_height = self.font.getbbox("A")[3] - self.font.getbbox("A")[1]
                total_text_height = len(wrapped_text) * line_height * 1.2
                y_text = self.tv_height - total_text_height - 60

                for line in wrapped_text:
                    bbox = draw.textbbox((0, 0), line, font=self.font)
                    line_width = bbox[2] - bbox[0]
                    x_text = (self.tv_width - line_width) / 2
                    draw.text((x_text, y_text), line, font=self.font, fill="white")
                    y_text += line_height * 1.2

                # 4. Salvar em formato otimizado
                output_path = self.output_dir / f"{output_filename}.webp"
                img.convert("RGB").save(output_path, "WEBP", quality=85)
                logging.info(f"Imagem processada e salva em: {output_path}")
                return output_path

        except httpx.RequestError as e:
            logging.error(f"Falha ao baixar a imagem {image_url}: {e}")
        except IOError as e:
            logging.error(f"Falha ao processar a imagem de {image_url} com Pillow: {e}")
        except Exception as e:
            logging.error(f"Erro inesperado ao processar {image_url}: {e}", exc_info=True)

        return None