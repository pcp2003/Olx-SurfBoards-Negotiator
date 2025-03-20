from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data

class ActionSelector(Component):
    display_name = "Action Selector"
    description = "Seleciona a ação apropriada baseada no contexto da conversa"
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "code"
    name = "ActionSelector"

    # Lista de ações permitidas
    ACOES_PERMITIDAS = [
        "buscar_pendentes",
        "enviar_mensagem",
        "receber_mensagem",
        "verificar_mensagem"
    ]

    inputs = [
        MessageTextInput(
            name="input",
            display_name="Input",
            info="Contexto ou instrução para selecionar a ação",
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

    def _determinar_acao(self, input_text: str) -> str:
        """Determina a ação apropriada baseada no input."""
        input_text = input_text.lower()
        
        # Se não houver input, buscar pendentes é a ação padrão
        if not input_text:
            return "buscar_pendentes"

        # Se estiver iniciando uma conversa
        if "iniciar" in input_text or "começar" in input_text or "novo" in input_text:
            return "buscar_pendentes"

        # Se estiver verificando uma mensagem
        if "verificar" in input_text or "checar" in input_text or "confirmar" in input_text:
            return "verificar_mensagem"

        # Se estiver respondendo uma mensagem
        if "responder" in input_text or "resposta" in input_text or "enviar" in input_text:
            return "enviar_mensagem"

        # Se estiver recebendo uma mensagem
        if "receber" in input_text or "nova mensagem" in input_text or "mensagem recebida" in input_text:
            return "receber_mensagem"

        # Se não conseguir determinar, buscar pendentes é a ação padrão
        return "buscar_pendentes"

    def process_inputs(self) -> Data:
        try:
            # Determinar a ação apropriada
            acao = self._determinar_acao(self.input)

            # Validar se a ação é permitida
            if acao not in self.ACOES_PERMITIDAS:
                return Data(value=f"Ação inválida: {acao}")

            data = Data(value=acao)
            self.status = data
            return data

        except Exception as e:
            return Data(value=f"Erro ao selecionar ação: {str(e)}") 