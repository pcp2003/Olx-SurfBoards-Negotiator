import json
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data


class ProcessaConversa(Component):
    display_name = "Processa Conversa"
    description = "Extrai informações de conversas de um JSON e trata valores nulos."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "chat"
    name = "ProcessaConversa"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="JSON de Conversa",
            info="Insira um JSON de conversas como string",
            value="{}",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Dados Extraídos", name="output", method="build_output"),
    ]

    def build_output(self) -> Data:
        try:
            # Converte a string JSON para um dicionário Python
            data = json.loads(self.input_value)

            # Pega a primeira conversa (se existir)
            conversa = data.get("conversas", [{}])[0]

            # Extrai os valores e trata valores nulos
            anuncio_id = conversa.get("anuncio_id", "ID não disponível")
            titulo_anuncio = conversa.get("titulo_anuncio", "Título não disponível")
            nome_vendedor = conversa.get("nome_vendedor", "Vendedor desconhecido")
            preco_anuncio = conversa.get("preco_anuncio", "Preço não informado")
            searched_info = conversa.get("searched_info", "") or ""  # Converte None para string vazia

            # Obtém a lista de mensagens (ou uma lista vazia)
            mensagens = conversa.get("mensagens", [])

            # Filtra a última mensagem recebida
            ultima_mensagem = next(
                (m.get("mensagem", "Sem mensagem") for m in mensagens if m.get("tipo") == "recebida"),
                "Nenhuma mensagem recebida"
            )

            # Retorna os dados no formato Data do Langflow
            return Data(
                value={
                    "anuncio_id": anuncio_id,
                    "titulo_anuncio": titulo_anuncio,
                    "nome_vendedor": nome_vendedor,
                    "preco_anuncio": preco_anuncio,
                    "searched_info": searched_info,
                }
            )

        except Exception as e:
            return Data(
                value={
                    "anuncio_id": "erro",
                    "titulo_anuncio": "erro",
                    "nome_vendedor": "erro",
                    "preco_anuncio": "erro",
                    "searched_info": str(e),
                }
            ) 