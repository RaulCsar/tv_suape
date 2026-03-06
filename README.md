# TV Suape - Mural Digital Corporativo

## 1. Visão Geral

O `tv_suape` é um sistema de Digital Signage (Mural Digital) refatorado para exibir as notícias mais recentes do Complexo Industrial Portuário de Suape de forma automatizada. O sistema é projetado para ser resiliente, eficiente e de fácil manutenção.

O sistema funciona como um pipeline que:
1.  **Extrai** notícias de múltiplas fontes (LinkedIn via Playwright e Site Institucional como fallback).
2.  **Processa** as manchetes sobre as imagens de fundo usando Pillow, otimizando-as para a web (WebP).
3.  **Renderiza** um site estático com Reveal.js e Jinja2, criando um carrossel de slides.
4.  **Automatiza** todo o processo com GitHub Actions, que executa o pipeline, commita as novas imagens e aciona o deploy na Vercel.

O projeto foi projetado para ser hospedado na Vercel, com um processo de CI/CD totalmente automatizado.

## 2. Arquitetura e Fluxo de Dados

O pipeline é orquestrado pelo `src/main.py` e segue os princípios SOLID, com clara separação de responsabilidades.

1.  **CI/CD (GitHub Actions)**:
    *   Um agendamento (`cron`) executa o workflow a cada 6 horas.
    *   O job instala as dependências, incluindo os navegadores do Playwright.
    *   Executa o orquestrador `src/main.py`.
    *   Commita e envia as alterações (novas imagens e `index.html`) para a branch principal, acionando o deploy na Vercel.

2.  **Orquestrador (`src/main.py`)**:
    *   Limpa o cache de imagens antigas em `assets/news/`.
    *   Instancia e executa os scrapers (`LinkedInSuapeScraper` e `SiteSuapeScraper`).
    *   Unifica e remove notícias duplicadas.
    *   Invoca o `ImageProcessor` para cada notícia.
    *   Invoca o `StaticSiteRenderer` para gerar o `index.html`.

3.  **Camada de Extração (`src/scrapers/`)**:
    *   `base.py`: Define a interface `Scraper` que todos os scrapers devem implementar (DIP).
    *   `linkedin_scraper.py`: Usa Playwright para acessar o LinkedIn de forma autenticada (via cookie em `secrets`) e extrair posts.
    *   `site_scraper.py`: Usa `httpx` e `BeautifulSoup4` para extrair notícias do site institucional como alternativa.

4.  **Camada de Engine (`src/engine/`)**:
    *   `processor.py`: Baixa a imagem, recorta para 16:9, aplica um gradiente e renderiza a manchete com `textwrap`. Salva em formato WebP em `assets/news/`.
    *   `renderer.py`: Usa `Jinja2` para renderizar o `templates/index.html.j2` com a lista de imagens geradas, criando o `index.html` na raiz.

## 3. Estrutura do Projeto (Arquitetura Alvo)

```plaintext
tv_suape/
├── .github/workflows/sync_pipeline.yml # Workflow de CI/CD
├── src/
│   ├── scrapers/
│   │   ├── base.py                     # Interface do Scraper (ABC)
│   │   ├── site_scraper.py             # Scraper do site institucional
│   │   └── linkedin_scraper.py         # Scraper do LinkedIn (Playwright)
│   ├── engine/
│   │   ├── processor.py                # Processador de Imagens (Pillow)
│   │   └── renderer.py                 # Renderizador de HTML (Jinja2)
│   └── main.py                         # Orquestrador do Pipeline
├── assets/
│   ├── news/                           # Destino das imagens processadas (cache)
│   └── fonts/                          # Fontes TrueType (ex: Roboto-Bold.ttf)
├── templates/
│   └── index.html.j2                   # Template HTML com Reveal.js
├── .env.example                        # Exemplo de variáveis de ambiente
├── requirements.txt                    # Dependências Python
└── index.html                          # Arquivo final gerado, deployado pela Vercel
```

## 4. Como Executar Localmente

### Pré-requisitos
*   Python 3.8+
*   `pip`

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/RaulCsar/tv_suape.git
    cd tv_suape
    ```

2.  **Crie um ambiente virtual e ative-o:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux / macOS
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

### Execução

Para rodar todo o pipeline (scraping, processamento de imagens e geração do HTML), execute o script principal:

```bash
python scraper.py
```

Após a execução, o site estará pronto dentro da pasta `public`. Você pode abrir o arquivo `public/index.html` em um navegador para ver o resultado.

## 5. Deploy (Vercel)

O deploy é automatizado e contínuo através da integração com a Vercel.

*   **Gatilho**: Qualquer `push` para a branch `main` no repositório do GitHub.
*   **Processo**:
    1.  A Vercel detecta o push e inicia um novo build.
    2.  O comando definido no `vercel.json` (`bash build.sh`) é executado.
    3.  O `build.sh` instala as dependências Python e executa o `scraper.py`, que gera os artefatos estáticos (imagens e `index.html`).
    4.  A Vercel publica o conteúdo do `outputDirectory` (`public`) no domínio de produção.

Essa arquitetura garante que, para atualizar as notícias na TV, basta que o pipeline seja executado e as alterações sejam enviadas ao repositório. Uma futura implementação envolve agendar a execução do `scraper.py` via GitHub Actions para automatizar 100% do processo.
