import os
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
from renderizador_noticias import preparar_imagem_tv

load_dotenv()

gemini_api_key = os.getenv("my_gemini_api_key")
# Configurações iniciais
BASE_URL = "https://www.suape.pe.gov.br"
PAGE_URL = f"{BASE_URL}/pt/"
OUTPUT_DIR = "imagens_noticias"
CSV_FILE = "noticias_suape.csv"

def main():
    # Cria a pasta para as imagens se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Pasta '{OUTPUT_DIR}' criada com sucesso.")

    print(f"Acessando a página: {PAGE_URL}")
    try:
        # Faz a requisição para a página principal
        response = requests.get(PAGE_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao acessar a página principal: {e}")
        return

    # Faz o parse do HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Encontra todos os cards de notícias
    cards = soup.find_all('article', class_='suape-card')
    
    if not cards:
        print("Nenhum card de notícia encontrado. Verifique a estrutura da página.")
        return

    print(f"Encontrados {len(cards)} cards de notícias.\n")

    # Prepara o arquivo CSV para salvar as manchetes e links
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Manchete', 'Link da Notícia', 'Link da Imagem', 'Caminho Local da Imagem'])

        for index, card in enumerate(cards, start=1):
            # 1. Extrai a manchete e o link da notícia
            title_tag = card.find('h4', class_='title')
            if not title_tag:
                continue
            
            a_tag = title_tag.find('a')
            if not a_tag:
                continue
            
            manchete = a_tag.get_text(strip=True)
            link_noticia_relativo = a_tag.get('href', '')
            link_noticia = urljoin(BASE_URL, link_noticia_relativo)

            # 2. Extrai a imagem
            img_tag = card.find('img', class_='imagens-not-home')
            if not img_tag:
                continue
            
            img_src_relativo = img_tag.get('src', '')
            img_url = urljoin(BASE_URL, img_src_relativo)

            # Define o nome do arquivo da imagem baseado na URL
            img_filename = img_url.split('/')[-1]
            if not img_filename:
                img_filename = f"imagem_generica_{index}.jpg"
            
            img_filepath = os.path.join(OUTPUT_DIR, img_filename)

            # 3. Faz o download da imagem com tratamento de exceções
            try:
                img_response = requests.get(img_url, stream=True, timeout=10)
                img_response.raise_for_status()
                
                with open(img_filepath, 'wb') as img_file:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        img_file.write(chunk)
                status_imagem = "Salva com sucesso"
                
                # 3.1. Prepara a imagem para a TV
                print(f"   -> Preparando imagem para TV...")
                sucesso_tv = preparar_imagem_tv(img_filepath, manchete)
                if sucesso_tv:
                    status_imagem += " e formatada para TV"
                else:
                    status_imagem += " (Erro ao formatar para TV)"
                    
            except requests.RequestException as e:
                print(f"[{index}] Erro ao baixar a imagem {img_url}: {e}")
                status_imagem = "Erro no download"
                img_filepath = ""

            # 4. Salva os dados no CSV
            writer.writerow([manchete, link_noticia, img_url, img_filepath])
            
            # Exibe o progresso no terminal
            print(f"Notícia {index}:")
            print(f" - Manchete: {manchete}")
            print(f" - Imagem: {status_imagem} ({img_filepath})\n")

    print(f"Extração concluída! Dados salvos em '{CSV_FILE}' e imagens na pasta '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    main()
