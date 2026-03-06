from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScraper(ABC):
    """
    Interface base para os scrapers de notícias.
    Garante que todos os scrapers obedeçam a um contrato unificado.
    """
    
    @abstractmethod
    def get_news(self) -> List[Dict[str, Any]]:
        """
        Extrai as notícias.
        
        Returns:
            List[Dict[str, Any]]: Uma lista de dicionários, sendo que cada
            dicionário deve conter no mínimo as chaves:
                - title (str): Título ou manchete
                - image_url (str): URL da imagem
                - source (str): Fonte da notícia (ex: 'Site Oficial', 'LinkedIn')
        """
        pass
