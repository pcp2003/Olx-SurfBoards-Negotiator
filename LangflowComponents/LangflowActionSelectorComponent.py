from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data

class ActionSelector(Component):
    display_name = "Action Selector"
    description = "Componente para selecionar a ação a ser executada baseado no contexto da conversa"
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "code"
    name = "ActionSelector"

    # Lista de ações permitidas
    ACOES_PERMITIDAS = [
        "buscar_conversas_pendentes",
        "buscar_mensagens",
        "enviar_mensagem"
    ]

    inputs = [
        MessageTextInput(
            name="input",
            display_name="Input",
            info="Input para determinar a ação a ser executada",
            value="",
            tool_mode=True
        )
    ]

    outputs = [
        Output(
            display_name="Ação Selecionada",
            name="acao_selecionada",
            method="process_inputs"
        )
    ]

    def process_inputs(self) -> Data:
        try:
            # Se o input contiver palavras-chave relacionadas a buscar conversas pendentes
            if any(palavra in self.input.lower() for palavra in ["pendentes", "novas", "não respondidas", "não respondido", "conversas pendentes"]):
                return Data(value="buscar_conversas_pendentes")
            
            # Se o input contiver palavras-chave relacionadas a buscar mensagens
            if any(palavra in self.input.lower() for palavra in ["buscar", "procurar", "encontrar", "listar", "ver", "mostrar", "histórico"]):
                return Data(value="buscar_mensagens")
            
            # Se o input contiver palavras-chave relacionadas a enviar mensagem
            if any(palavra in self.input.lower() for palavra in ["enviar", "mandar", "responder", "resposta", "mensagem"]):
                return Data(value="enviar_mensagem")
            
            # Se não encontrar nenhuma palavra-chave, retorna buscar_conversas_pendentes como padrão
            return Data(value="buscar_conversas_pendentes")

        except Exception as e:
            return Data(value=f"Erro: {str(e)}") 