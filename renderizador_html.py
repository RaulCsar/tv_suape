import logging
from pathlib import Path
from typing import List
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PainelRenderer:
    """
    Classe responsável por ler as imagens do diretório, e compilá-las num template Jinja2 (Reveal.js)
    gerando o artefato final HTML (Presentation Layer).
    """

    def __init__(
        self, 
        imagens_dir: Path, 
        template_path: Path, 
        output_file: Path, 
        slide_duration_ms: int = 10000
    ) -> None:
        self.imagens_dir = imagens_dir
        self.template_path = template_path
        self.output_file = output_file
        self.slide_duration_ms = slide_duration_ms

    def _obter_imagens(self) -> List[str]:
        """
        Varre o diretório configurado, retornando a lista de caminhos relativos ao index.html gerado.
        
        Returns:
            List[str]: Lista com caminhos relativos das imagens.
        """
        if not self.imagens_dir.exists() or not self.imagens_dir.is_dir():
            logger.warning(f"O diretório de imagens '{self.imagens_dir}' não existe ou não é um diretório válido.")
            return []

        # Buscando arquivos de imagem (permitindo as extensões mais comuns do projeto)
        imagens: List[Path] = []
        for extensao in ('*.jpg', '*.jpeg', '*.png'):
            imagens.extend(self.imagens_dir.glob(extensao))

        # Precisamos passar o caminho relativo da imagem para o documento HTML (eg: imagens_tv/tv_noticia.jpg)
        paths_relativos: List[str] = []
        # O HTML final será renderizado no diretório pai do output_file (ou o diretório de execução atual da aplicação)
        # Assumindo que o HTML ficará lado a lado da pasta `imagens_tv` na pasta `public`
        try:
            cwd_relativo_ao_html = self.output_file.parent.absolute()
            for img in imagens:
                # Resolve caminhos relativos ao arquivo final HTML
                caminho_relativo = img.absolute().relative_to(cwd_relativo_ao_html)
                # Garante formato com barras normais independente de SO (Windows usa contra-barra) e remove 'public/' se existir
                path_str = caminho_relativo.as_posix()
                paths_relativos.append(path_str)
        except ValueError as e:
            logger.error(f"Erro de resolução de caminhos relativos: {e}")
            return []

        logger.info(f"{len(paths_relativos)} imagens encontradas para renderização.")
        return sorted(paths_relativos)

    def renderizar(self) -> bool:
        """
        Executa o fluxo completo: obtém as imagens, preenche e salva o template renderizado.
        
        Returns:
            bool: True se teve sucesso, False em caso de falhas.
        """
        # 1. Validações preliminares do Template
        if not self.template_path.exists():
            logger.error(f"Arquivo de template '{self.template_path}' não foi encontrado.")
            return False

        # 2. Configura e carrega o template Jinja enviando dados de contexto
        template_dir = self.template_path.parent
        template_name = self.template_path.name

        try:
            env = Environment(loader=FileSystemLoader(str(template_dir.absolute())))
            template = env.get_template(template_name)
        except TemplateNotFound:
            logger.error(f"Jinja template loader não encontrou: {template_name} em {template_dir}")
            return False
        except Exception as e:
            logger.error(f"Erro ao inicializar o Jinja Environment: {e}")
            return False

        imagens_relativas = self._obter_imagens()
        
        # 3. Compilação
        context = {
            "images": imagens_relativas,
            "slide_duration_ms": self.slide_duration_ms
        }
        
        try:
            html_renderizado = template.render(context)
        except Exception as e:
            logger.error(f"Erro compilando o template Jinja2: {e}")
            return False

        # 4. Escrita do resultado (IO Seguro)
        try:
            # Em Python 3.9+ usamos write_text(), e permitimos setar encoding
            self.output_file.write_text(html_renderizado, encoding="utf-8")
            logger.info(f"Painel HTML compilado com sucesso em '{self.output_file}'.")
            return True
        except PermissionError:
            logger.error(f"Permissão negada ao tentar salvar o arquivo em '{self.output_file}'.")
        except IOError as e:
            logger.error(f"Falha de I/O escrevendo o HTML final: {e}")
        
        return False
