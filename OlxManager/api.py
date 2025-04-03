import logging
import requests
import time
from typing import Dict, Any, Optional

from config import CREDENTIALS

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self, api_url: str):
        self.api_url = api_url
        logger.info(f"API URL configurada: {self.api_url}")

    def verificar_mensagem_existe(self, anuncio_id: str, mensagem: str, tipo: str) -> bool:
        """Verifica se uma mensagem já existe na DB antes de enviá-la para a API"""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                response = requests.get(
                    f"{self.api_url}/mensagem-existe",
                    params={
                        "email": CREDENTIALS["username"],
                        "anuncio_id": anuncio_id,
                        "mensagem": mensagem,
                        "tipo": tipo
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json().get("existe", False)
                elif response.status_code == 404:
                    logger.warning("Endpoint de verificação de mensagem não encontrado")
                    return False
                else:
                    logger.error(f"Erro ao verificar mensagem na API: {response.text}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(2)
            except requests.exceptions.Timeout:
                logger.error(f"Timeout ao verificar mensagem (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except requests.exceptions.ConnectionError:
                logger.error(f"Erro de conexão ao verificar mensagem (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Tentativa {tentativa + 1} falhou: {e}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
        return False

    def enviar_mensagem_para_api(self, anuncio_id: str, mensagem: str, tipo: str) -> bool:
        """Envia uma mensagem extraída pelo scraper para a API FastAPI"""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                payload = {"mensagem": mensagem}
                response = requests.post(
                    f"{self.api_url}/receber-mensagem",
                    json=payload,
                    params={
                        "email": CREDENTIALS["username"],
                        "anuncio_id": anuncio_id,
                        "tipo": tipo
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"Mensagem {tipo} registrada na API: {mensagem}")
                    return True
                elif response.status_code == 404:
                    logger.warning("Endpoint de envio de mensagem não encontrado")
                    return False
                else:
                    logger.error(f"Erro ao registrar mensagem na API: {response.text}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(2)
            except requests.exceptions.Timeout:
                logger.error(f"Timeout ao enviar mensagem (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except requests.exceptions.ConnectionError:
                logger.error(f"Erro de conexão ao enviar mensagem (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Tentativa {tentativa + 1} falhou: {e}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
        return False

    def buscar_respostas_pendentes(self):
        """ Busca conversas com mensagens recebidas não respondidas na API """
        try:
            response = requests.get(
                f"{self.api_url}/conversas/pendentes",
                params={"email": CREDENTIALS["username"]},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("conversas_pendentes", [])
            elif response.status_code == 404:
                logger.warning("Endpoint de conversas pendentes não encontrado")
                return []
            else:
                logger.error(f"Erro ao buscar conversas pendentes: {response.text}")
                return []
        except requests.exceptions.Timeout:
            logger.error("Timeout ao buscar conversas pendentes")
            return []
        except requests.exceptions.ConnectionError:
            logger.error("Erro de conexão ao buscar conversas pendentes")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar conversas pendentes: {e}")
            return []

    def enviar_info_anuncio_para_api(self, anuncio_id: str, nome_vendedor: str, titulo_anuncio: str, preco_anuncio: str) -> bool:
        """Envia informações do anúncio para a API"""
        try:
            response = requests.post(
                f"{self.api_url}/atualizar-info-anuncio",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id,
                    "nome_vendedor": nome_vendedor,
                    "titulo_anuncio": titulo_anuncio,
                    "preco_anuncio": preco_anuncio
                },
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"Informações do anúncio {anuncio_id} atualizadas com sucesso")
                return True
            else:
                logger.error(f"Erro ao atualizar informações do anúncio: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erro ao enviar informações do anúncio para a API: {e}")
            return False

    def atualizar_searched_info(self, anuncio_id: str, searched_info: str) -> bool:
        """Atualiza o campo searched_info do anúncio na API"""
        try:
            response = requests.post(
                f"{self.api_url}/atualizar-searched-info",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id,
                    "searched_info": searched_info
                },
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"Campo searched_info do anúncio {anuncio_id} atualizado com sucesso")
                return True
            elif response.status_code == 404:
                logger.warning(f"Conversa não encontrada para o anúncio {anuncio_id}")
                return False
            else:
                logger.error(f"Erro ao atualizar searched_info do anúncio: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erro ao enviar searched_info para a API: {e}")
            return False

    def buscar_info_anuncio(self, anuncio_id: str) -> Optional[Dict[str, Any]]:
        """Busca informações do anúncio na API"""
        try:
            response = requests.get(
                f"{self.api_url}/info-anuncio",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Informações do anúncio {anuncio_id} não encontradas")
                return None
            else:
                logger.error(f"Erro ao buscar informações do anúncio: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar informações do anúncio na API: {e}")
            return None 