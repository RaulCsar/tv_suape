import logging
import requests
import textwrap
from pathlib import Path
from typing import Dict, Any, Optional
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, output_dir: Path, target_size: tuple = (1920, 1080)):
        self.output_dir = output_dir
        self.target_size = target_size
        self._ensure_output_dir()
        
    def _ensure_output_dir(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _create_gradient(self, width: int, height: int, start_color: tuple, end_color: tuple) -> Image.Image:
        """Cria um gradiente vertical."""
        base = Image.new('RGBA', (width, height), start_color)
        top = Image.new('RGBA', (width, height), end_color)
        mask = Image.new('L', (width, height))
        mask_data = []
        for y in range(height):
            mask_data.extend([int(255 * (y / height))] * width)
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

    def process_news_item(self, news: Dict[str, Any], index: int) -> Optional[str]:
        """
        Baixa a imagem, aplica resize/crop, adiciona o gradiente na base, 
        renderiza o texto formatado (wrap text) e salva em WebP.
        """
        try:
            logger.info(f"Processando imagem para: '{news['title'][:30]}...'")
            response = requests.get(news['image_url'], timeout=15)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            
            # Redimensionar / Crop centralizado
            img_aspect = img.width / img.height
            target_aspect = self.target_size[0] / self.target_size[1]
            
            if img_aspect > target_aspect:
                # Imagem muito larga
                new_width = int(img.height * target_aspect)
                left = (img.width - new_width) / 2
                img = img.crop((left, 0, left + new_width, img.height))
            elif img_aspect < target_aspect:
                # Imagem muito alta
                new_height = int(img.width / target_aspect)
                top = (img.height - new_height) / 2
                img = img.crop((0, top, img.width, top + new_height))
                
            img = img.resize(self.target_size, Image.Resampling.LANCZOS)
            
            # Criar a sobreposição do gradiente na parte inferior (40% da imagem)
            gradient_height = int(self.target_size[1] * 0.4)
            gradient = self._create_gradient(
                self.target_size[0], gradient_height, 
                (0, 0, 0, 0), (0, 0, 0, 220)
            )
            img.paste(gradient, (0, self.target_size[1] - gradient_height), gradient)
            
            # Escrever o título da notícia
            draw = ImageDraw.Draw(img)
            # Tentar carregar fonte, usar fonte default se não encontrar TTF system
            try:
                # Pode apontar para uma fonte em assets se necessário
                font = ImageFont.truetype("arialbd.ttf", 60)
            except IOError:
                font = ImageFont.load_default(size=40)
            
            # Text Wrap para evitar ultrapassar bordas
            margin = 80
            max_width = self.target_size[0] - 2 * margin
            wrapped_text = textwrap.fill(news['title'], width=50) # TBD largura baseada no ttf
            
            # Calcular o tamanho do texto (box) aproximado
            bbox = draw.textbbox((0, 0), wrapped_text, font=font)
            text_height = bbox[3] - bbox[1]
            
            # Posicionar perto da base
            text_x = margin
            text_y = self.target_size[1] - text_height - 60
            
            # Sombra simples
            draw.text((text_x + 3, text_y + 3), wrapped_text, font=font, fill=(0, 0, 0, 180))
            draw.text((text_x, text_y), wrapped_text, font=font, fill=(255, 255, 255, 255))
            
            output_filename = f"slide_{index:02d}.webp"
            output_filepath = self.output_dir / output_filename
            
            final_img = img.convert("RGB") # WebP não necessita alpha no nosso caso estático
            final_img.save(output_filepath, format="WEBP", quality=85, method=6)
            
            logger.info(f"Salvo sucesso: {output_filepath}")
            return output_filepath.name
                
        except requests.RequestException as e:
            logger.error(f"Erro no download da imagem {news['image_url']}: {e}")
        except Exception as e:
            logger.exception(f"Erro ao processar a imagem da notícia '{news['title']}': {e}")
            
        return None