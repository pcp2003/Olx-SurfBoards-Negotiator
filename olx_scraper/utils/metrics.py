from datetime import datetime
from typing import Dict, Any
from utils.logger import logger

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

    def log_metricas(self) -> None:
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

    def iniciar_execucao(self):
        """Inicia a contagem de tempo de execução"""
        self.metricas['inicio_execucao'] = datetime.now()

    def atualizar_tempo_execucao(self):
        """Atualiza o tempo total de execução"""
        if self.metricas['inicio_execucao']:
            self.metricas['ultima_verificacao'] = datetime.now()
            self.metricas['tempo_total_execucao'] = (
                self.metricas['ultima_verificacao'] - 
                self.metricas['inicio_execucao']
            ).total_seconds() 