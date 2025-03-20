import requests
import json
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data

class FastAPIClient(Component):
    display_name = "FastAPI Client"
    description = "Componente para acessar APIs do FastAPI e interagir com a DB"
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "code"
    name = "FastAPIClient"

    # Lista de ações permitidas
    ACOES_PERMITIDAS = [
        "buscar_pendentes",
        "enviar_mensagem",
        "receber_mensagem",
        "verificar_mensagem",
        "buscar_mensagens"
    ]

    # Lista de tipos permitidos
    TIPOS_PERMITIDOS = ["recebida", "enviada"]

    inputs = [
        MessageTextInput(
            name="acao",
            display_name="Ação",
            info="Ação a ser executada (buscar_pendentes, enviar_mensagem, receber_mensagem, verificar_mensagem, buscar_mensagens)",
            value="",
            tool_mode=True
        ),
        MessageTextInput(
            name="email",
            display_name="Email",
            info="Email do usuário",
            value="",
            tool_mode=True
        ),
        MessageTextInput(
            name="anuncio_id",
            display_name="ID do Anúncio",
            info="ID do anúncio (não necessário para buscar_pendentes e buscar_mensagens)",
            value="",
            tool_mode=True
        ),
        MessageTextInput(
            name="mensagem",
            display_name="Mensagem",
            info="Texto da mensagem (necessário para enviar_mensagem e receber_mensagem)",
            value="",
            tool_mode=True
        ),
        MessageTextInput(
            name="tipo",
            display_name="Tipo",
            info="Tipo da mensagem (recebida/enviada) - necessário para receber_mensagem, verificar_mensagem e buscar_mensagens",
            value="",
            tool_mode=True
        ),
        MessageTextInput(
            name="conversa_id",
            display_name="ID da Conversa",
            info="ID da conversa para filtrar mensagens (opcional)",
            value="",
            tool_mode=True
        ),
        MessageTextInput(
            name="respondida",
            display_name="Status de Resposta",
            info="Status de resposta da mensagem (true/false) - opcional para buscar_mensagens",
            value="",
            tool_mode=True
        )
    ]

    outputs = [
        Output(
            display_name="Resposta da API",
            name="api_response",
            method="process_inputs"
        )
    ]

    def process_inputs(self) -> Data:
        try:
            # Configuração base
            base_url = "http://localhost:8000"
            headers = {"Content-Type": "application/json"}

            # Validação da ação
            if self.acao not in self.ACOES_PERMITIDAS:
                return Data(value=f"Ação inválida. Ações permitidas: {', '.join(self.ACOES_PERMITIDAS)}")

            # Validação do tipo (se fornecido)
            if self.tipo and self.tipo not in self.TIPOS_PERMITIDOS:
                return Data(value=f"Tipo inválido. Tipos permitidos: {', '.join(self.TIPOS_PERMITIDOS)}")

            # Mapeamento de ações para endpoints e métodos
            acoes = {
                "buscar_pendentes": {
                    "endpoint": "conversas/pendentes",
                    "method": "GET",
                    "params": {"email": self.email}
                },
                "enviar_mensagem": {
                    "endpoint": "enviar-mensagem",
                    "method": "POST",
                    "params": {
                        "email": self.email,
                        "anuncio_id": self.anuncio_id
                    },
                    "data": {"mensagem": self.mensagem}
                },
                "receber_mensagem": {
                    "endpoint": "receber-mensagem",
                    "method": "POST",
                    "params": {
                        "email": self.email,
                        "anuncio_id": self.anuncio_id,
                        "tipo": self.tipo
                    },
                    "data": {"mensagem": self.mensagem}
                },
                "verificar_mensagem": {
                    "endpoint": "mensagem-existe",
                    "method": "GET",
                    "params": {
                        "email": self.email,
                        "anuncio_id": self.anuncio_id,
                        "mensagem": self.mensagem,
                        "tipo": self.tipo
                    }
                },
                "buscar_mensagens": {
                    "endpoint": "mensagens",
                    "method": "GET",
                    "params": {
                        "email": self.email,
                        "tipo": self.tipo if self.tipo else None,
                        "conversa_id": int(self.conversa_id) if self.conversa_id else None,
                        "anuncio_id": self.anuncio_id if self.anuncio_id else None,
                        "respondida": bool(self.respondida.lower() == "true") if self.respondida else None
                    }
                }
            }

            acao_config = acoes[self.acao]
            
            # Validação de parâmetros específicos
            if self.acao not in ["buscar_pendentes", "buscar_mensagens"] and not self.anuncio_id:
                return Data(value="ID do anúncio é obrigatório para esta ação")
            
            if self.acao in ["enviar_mensagem", "receber_mensagem"] and not self.mensagem:
                return Data(value="Mensagem é obrigatória para esta ação")
            
            if self.acao in ["receber_mensagem", "verificar_mensagem"] and not self.tipo:
                return Data(value="Tipo é obrigatório para esta ação")

            # Realizar a requisição
            url = f"{base_url}/{acao_config['endpoint']}"
            method = acao_config['method']
            params = acao_config.get('params')
            data = acao_config.get('data')

            if method == "GET":
                response = requests.get(url, params=params, headers=headers)
            else:
                response = requests.post(url, params=params, json=data, headers=headers)

            response.raise_for_status()
            data = Data(value=json.dumps(response.json(), ensure_ascii=False))
            self.status = data
            return data

        except requests.exceptions.RequestException as e:
            return Data(value=f"Erro na requisição: {str(e)}")
        except Exception as e:
            return Data(value=f"Erro: {str(e)}")
