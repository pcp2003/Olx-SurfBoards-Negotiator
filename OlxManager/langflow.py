import logging
import time
import requests
import uuid
from typing import Optional

from config import URLS, CREDENTIALS

logger = logging.getLogger(__name__)

class LangflowManager:
    def __init__(self):
        self.langflow_url = URLS["Langflow_URL"].replace("/predict/", "/run/")
        logger.info(f"Langflow URL configurada: {self.langflow_url}")

    def obter_resposta(self, mensagem: str, anuncio_id: str, session_id: Optional[str] = None) -> Optional[str]:
        """
        Envia a mensagem para o Langflow e obtém a resposta.
        
        Args:
            mensagem (str): A mensagem a ser processada pelo Langflow
            anuncio_id (str): ID do anúncio para buscar histórico
            session_id (str, optional): ID da sessão existente. Se None, gera um novo.
            
        Returns:
            Optional[str]: A resposta do Langflow ou None em caso de falha
        """
        if not mensagem or not isinstance(mensagem, str):
            logger.error("Mensagem inválida fornecida para o Langflow")
            return None
            
        try:
            # Buscar informações do anúncio
            logger.info(f"Buscando informações do anúncio {anuncio_id}")
            response = requests.get(
                f"{URLS['api']}/info-anuncio",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id
                },
                timeout=10
            )
            
            info_anuncio = {}
            if response.status_code == 200:
                info_anuncio = response.json()
                logger.info(f"Informações do anúncio encontradas: {info_anuncio}")
            else:
                logger.warning(f"Erro ao buscar informações do anúncio: {response.text}")
            
            # Preparar input_value com as informações do anúncio
            input_value = f"{anuncio_id},{info_anuncio.get('titulo_anuncio', '')},{info_anuncio.get('nome_vendedor', '')},{info_anuncio.get('preco_anuncio', '')},{mensagem}"
            
            # Log do input_value exato
            logger.info(f"\ninput_value = {input_value}\n")
            
            logger.info(f"Obtendo resposta para a mensagem: {mensagem}")
            
            # Usa session_id existente ou gera um novo
            current_session_id = session_id if session_id else str(uuid.uuid4())
            
            # Payload simplificado sem histórico
            payload = {
                "input_value": input_value,
                "output_type": "chat",
                "input_type": "chat",
                "tweaks": {
                    "ChatOutput-trXWe": {},
                    "GetEnvVar-fD5AB": {},
                    "CustomComponent-ZQxeP": {},
                    "CustomComponent-iJBo4": {},
                    "Agent-tIIK7": {},
                    "ChatInput-g5RAZ": {},
                    "Prompt-F7ylB": {}
                }
            }
            
            max_tentativas = 3
            tempo_espera_base = 5  # Tempo base de espera em segundos
            
            for tentativa in range(max_tentativas):
                try:
                    response = requests.post(
                        self.langflow_url, 
                        json=payload,
                        timeout=30,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }
                    )

                    if response.status_code == 200:
                        resposta_json = response.json()
                        logger.debug(f"Resposta completa do Langflow: {resposta_json}")
                        
                        # Extração robusta da mensagem de resposta
                        try:
                            # Caminho principal baseado na estrutura do JSON fornecido
                            if 'outputs' in resposta_json:
                                for output in resposta_json['outputs']:
                                    if 'outputs' in output:
                                        for sub_output in output['outputs']:
                                            if 'results' in sub_output:
                                                results = sub_output['results']
                                                if 'message' in results:
                                                    message_data = results['message']
                                                    if isinstance(message_data, dict):
                                                        # Tenta obter o texto da resposta em vários caminhos possíveis
                                                        if 'data' in message_data and 'text' in message_data['data']:
                                                            return message_data['data']['text']
                                                        elif 'text' in message_data:
                                                            return message_data['text']
                                                        elif 'message' in message_data:
                                                            return message_data['message']
                            
                            # Fallback para caminhos alternativos
                            if 'message' in resposta_json:
                                if isinstance(resposta_json['message'], dict):
                                    if 'text' in resposta_json['message']:
                                        return resposta_json['message']['text']
                                    elif 'data' in resposta_json['message'] and 'text' in resposta_json['message']['data']:
                                        return resposta_json['message']['data']['text']
                                elif isinstance(resposta_json['message'], str):
                                    return resposta_json['message']
                            
                            # Último fallback: procura em toda a estrutura por um campo 'text'
                            if 'text' in resposta_json:
                                return resposta_json['text']
                            
                        except (KeyError, TypeError) as e:
                            logger.warning(f"Erro ao extrair resposta: {e}")
                        
                        logger.warning("Nenhuma resposta válida encontrada no JSON retornado")
                        return None
                    elif response.status_code == 429:  # Rate limit
                        tempo_espera = tempo_espera_base * (2 ** tentativa)  # Backoff exponencial
                        logger.warning(f"Rate limit atingido. Aguardando {tempo_espera} segundos antes da próxima tentativa...")
                        time.sleep(tempo_espera)
                        continue
                    else:
                        logger.error(f"Erro na requisição ao Langflow (status {response.status_code}): {response.text}")
                        if tentativa < max_tentativas - 1:
                            time.sleep(tempo_espera_base)
                        continue
                        
                except requests.exceptions.Timeout:
                    logger.error(f"Timeout na tentativa {tentativa + 1}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(tempo_espera_base)
                except requests.exceptions.ConnectionError:
                    logger.error(f"Erro de conexão na tentativa {tentativa + 1}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(tempo_espera_base)
                except Exception as e:
                    logger.error(f"Erro inesperado na tentativa {tentativa + 1}: {e}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(tempo_espera_base)
            
            return None
                
        except Exception as e:
            logger.error(f"Erro inesperado ao obter resposta do Langflow: {e}")
            return None 