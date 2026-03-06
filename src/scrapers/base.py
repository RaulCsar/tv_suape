import logging
from abc import ABC, abstractmethod
from typing import Dict, List


class Scraper(ABC):
    """
    Interface abstrata (Protocolo) para todos os Scrapers.
    Define um contrato único para a obtenção de notícias, garantindo que
    o orquestrador possa tratar diferentes fontes de dados de forma uniforme.
    """

    @abstractmethod
    def get_news(self) -> List[Dict[str, str]]:
        """Extrai notícias de uma fonte de dados e as retorna."""
        pass