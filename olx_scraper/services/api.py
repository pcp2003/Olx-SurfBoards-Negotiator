import requests
from typing import Dict, Any, List
from utils.logger import logger
from config.settings import CREDENTIALS
from models.anuncio import Anuncio, Mensagem

class APIService:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def criar_conversa(self, anuncio_id: str) -> bool:
        """Cria uma nova conversa no banco de dados"""
        try:
            response = requests.post(
                f"{self.api_url}/criar-conversa",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id
                },
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"Erro ao criar conversa: {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao criar conversa: {e}")
            return False

    def atualizar_info_anuncio(self, anuncio_id: str, info: Dict[str, str]) -> bool:
        """Atualiza informações do anúncio"""
        try:
            response = requests.post(
                f"{self.api_url}/atualizar-info-anuncio",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id,
                    **info
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

    def enviar_mensagem(self, anuncio_id: str, mensagem: str, tipo: str) -> bool:
        """Envia uma mensagem para a API"""
        try:
            response = requests.post(
                f"{self.api_url}/receber-mensagem",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id,
                    "tipo": tipo
                },
                json={"mensagem": mensagem},
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"Mensagem {tipo} registrada na API: {mensagem}")
                return True
            else:
                logger.error(f"Erro ao registrar mensagem na API: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para a API: {e}")
            return False

    def verificar_mensagem_existe(self, anuncio_id: str, mensagem: str, tipo: str) -> bool:
        """Verifica se uma mensagem já existe na API"""
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
            else:
                logger.error(f"Erro ao verificar mensagem na API: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erro ao verificar mensagem na API: {e}")
            return False

    def buscar_conversas_pendentes(self) -> List[Dict[str, Any]]:
        """Busca conversas com mensagens não respondidas"""
        try:
            response = requests.get(
                f"{self.api_url}/conversas/pendentes",
                params={"email": CREDENTIALS["username"]},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("conversas_pendentes", [])
            else:
                logger.error(f"Erro ao buscar conversas pendentes: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Erro ao buscar conversas pendentes: {e}")
            return []

    def buscar_info_anuncio(self, anuncio_id: str) -> Dict[str, str]:
        """Busca informações do anúncio"""
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
            else:
                logger.error(f"Erro ao buscar informações do anúncio: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Erro ao buscar informações do anúncio: {e}")
            return {} 