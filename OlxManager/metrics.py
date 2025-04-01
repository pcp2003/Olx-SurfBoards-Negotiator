import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

class MetricsManager:
    def __init__(self):
        self.metricas = {
            'mensagens_processadas': 0,
            'respostas_enviadas': 0,
            'erros': 0,
            'inicio_execucao': None,
            'ultima_verificacao': None,
            'tempo_total_execucao': 0
        }
        logger.info("Métricas inicializadas")

    def atualizar(self, tipo: str, valor: Any = 1) -> None:
        """Atualiza as métricas do scraper"""
        try:
            if tipo in self.metricas:
                if isinstance(self.metricas[tipo], (int, float)):
                    self.metricas[tipo] += valor
                    logger.debug(f"Métrica '{tipo}' atualizada para {self.metricas[tipo]}")
                else:
                    self.metricas[tipo] = valor
                    logger.debug(f"Métrica '{tipo}' definida para {valor}")
            else:
                logger.warning(f"Tipo de métrica desconhecido: {tipo}")
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")

    def log(self) -> None:
        """Registra as métricas atuais"""
        try:
            logger.info("=== Métricas do Scraper ===")
            for key, value in self.metricas.items():
                if isinstance(value, datetime):
                    logger.info(f"  {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logger.info(f"  {key}: {value}")
            logger.info("==========================")
        except Exception as e:
            logger.error(f"Erro ao registrar métricas: {e}") 