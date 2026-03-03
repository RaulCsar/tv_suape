import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

# Configurações da TV
TV_WIDTH = 1920
TV_HEIGHT = 1080
OUTPUT_DIR = "public/imagens_tv"

def preparar_imagem_tv(caminho_imagem, texto_manchete):
    """
    Redimensiona/recorta uma imagem para 1920x1080, adiciona uma tarja semi-transparente
    na parte inferior e escreve a manchete sobre ela.
    """
    # Cria a pasta de saída se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        # Abre a imagem original
        img = Image.open(caminho_imagem).convert("RGBA")
    except Exception as e:
        print(f"Erro ao abrir a imagem {caminho_imagem}: {e}")
        return False

    # 1. Redimensionar e Recortar (Crop) para 1920x1080 (Proporção 16:9)
    target_ratio = TV_WIDTH / TV_HEIGHT
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Imagem é mais larga que a proporção alvo: recorta as laterais
        new_width = int(target_ratio * img.height)
        offset = (img.width - new_width) // 2
        img = img.crop((offset, 0, img.width - offset, img.height))
    elif img_ratio < target_ratio:
        # Imagem é mais alta que a proporção alvo: recorta em cima e embaixo
        new_height = int(img.width / target_ratio)
        offset = (img.height - new_height) // 2
        img = img.crop((0, offset, img.width, img.height - offset))

    # Redimensiona para o tamanho exato da TV usando o filtro LANCZOS (alta qualidade)
    img = img.resize((TV_WIDTH, TV_HEIGHT), Image.Resampling.LANCZOS)

    # 2. Criar a tarja semi-transparente
    # Altura da tarja (ajustada para ficar menor e ocupar menos a imagem)
    tarja_height = 180
    tarja_y_start = TV_HEIGHT - tarja_height

    # Cria uma nova imagem transparente para desenhar a tarja
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Desenha o retângulo preto com 60% de opacidade (255 * 0.6 = ~153)
    draw.rectangle(
        [(0, tarja_y_start), (TV_WIDTH, TV_HEIGHT)],
        fill=(0, 0, 0, 153)
    )

    # Mescla a tarja com a imagem original
    img = Image.alpha_composite(img, overlay)

    # 3. Configurar a Fonte e o Texto
    # Garante que teremos uma fonte renderizável (tenta carregar da pasta local primeiro)
    import urllib.request
    
    tamanho_fonte = 60
    
    # Procura prioritariamente pela pasta de fontes embutida no repositório
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    if not os.path.exists(font_dir):
        os.makedirs(font_dir, exist_ok=True)
        
    font_path = os.path.join(font_dir, "Matt-Regular.ttf")
    
    # Fallback automático caso o usuário não tenha a fonte Matt no repositório
    if not os.path.exists(font_path):
        try:
            print("Aviso: Fonte Matt não encontrada no projeto.")
            print("Baixando fonte Roboto com fallback provisório da internet...")
            font_path = os.path.join(font_dir, "Roboto-Regular.ttf")
            if not os.path.exists(font_path):
                url_fonte = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
                urllib.request.urlretrieve(url_fonte, font_path)
        except Exception as e:
            print(f"Erro ao baixar a fonte de fallback: {e}")

    try:
        fonte = ImageFont.truetype(font_path, tamanho_fonte)
    except IOError:
        try:
            fonte = ImageFont.truetype("arial.ttf", tamanho_fonte)
        except IOError:
            print("Aviso: Nenhuma fonte TrueType funcionou. Usando padrão.")
            fonte = ImageFont.load_default()

    # Prepara o objeto de desenho na imagem final
    draw = ImageDraw.Draw(img)

    # Quebra o texto em múltiplas linhas se for muito longo
    # O valor 'width' (ex: 50) depende do tamanho da fonte e da largura da tela
    linhas_texto = textwrap.wrap(texto_manchete, width=55)

    # Calcula a altura total do bloco de texto para centralizá-lo verticalmente na tarja
    # Usamos textbbox para obter as dimensões do texto
    altura_linha = draw.textbbox((0, 0), "A", font=fonte)[3] - draw.textbbox((0, 0), "A", font=fonte)[1]
    espacamento_linhas = 10
    altura_total_texto = (len(linhas_texto) * altura_linha) + ((len(linhas_texto) - 1) * espacamento_linhas)

    # Posição Y inicial do texto (centralizado dentro da tarja)
    y_texto = tarja_y_start + (tarja_height - altura_total_texto) // 2

    # 4. Desenhar o texto na imagem
    for linha in linhas_texto:
        # Calcula a largura da linha para centralizá-la horizontalmente
        largura_linha = draw.textbbox((0, 0), linha, font=fonte)[2] - draw.textbbox((0, 0), linha, font=fonte)[0]
        x_texto = (TV_WIDTH - largura_linha) // 2
        
        # Desenha o texto em branco
        draw.text((x_texto, y_texto), linha, font=fonte, fill=(255, 255, 255, 255))
        
        # Move o Y para a próxima linha
        y_texto += altura_linha + espacamento_linhas

    # 5. Salvar a imagem final
    # Converte de volta para RGB para salvar como JPEG
    img_final = img.convert("RGB")
    
    # Extrai o nome do arquivo original
    nome_arquivo = os.path.basename(caminho_imagem)
    caminho_saida = os.path.join(OUTPUT_DIR, f"tv_{nome_arquivo}")
    
    img_final.save(caminho_saida, "JPEG", quality=95)
    print(f"Imagem para TV salva em: {caminho_saida}")
    
    return True

# Exemplo de uso (para testes isolados)
if __name__ == "__main__":
    # Crie uma imagem de teste ou aponte para uma existente para testar o módulo
    print("Módulo renderizador_noticias carregado. Importe a função preparar_imagem_tv no seu scraper.")