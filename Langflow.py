import argparse
import json
from argparse import RawTextHelpFormatter
import requests
from typing import Optional
import warnings
try:
    from langflow.load import upload_file
except ImportError:
    warnings.warn("Langflow provides a function to help you upload files to the flow. Please install langflow to use it.")
    upload_file = None

BASE_API_URL = "http://127.0.0.1:7860"
FLOW_ID = "a0075945-5b70-43d4-9a82-ab84ddc6be27"
ENDPOINT = "" # You can set a specific endpoint name in the flow settings

# You can tweak the flow by adding a tweaks dictionary
# e.g {"OpenAI-XXXXX": {"model_name": "gpt-4"}}
TWEAKS = {
  "ChatOutput-trXWe": {
    "background_color": "",
    "chat_icon": "",
    "clean_data": True,
    "data_template": "{text}",
    "input_value": "",
    "sender": "Machine",
    "sender_name": "AI",
    "session_id": "",
    "should_store_message": True,
    "text_color": ""
  },
  "GetEnvVar-fD5AB": {
    "env_dir": "",
    "env_var_name": "",
    "tools_metadata": [
      {
        "name": "GetEnvVar-process_inputs",
        "description": "process_inputs() - Get env var from a specified directory",
        "tags": [
          "GetEnvVar-process_inputs"
        ]
      }
    ]
  },
  "CustomComponent-ZQxeP": {
    "acao": "",
    "anuncio_id": "",
    "conversa_id": "",
    "email": "",
    "mensagem": "",
    "respondida": "",
    "tipo": "",
    "tools_metadata": [
      {
        "name": "FastAPIClient-process_inputs",
        "description": "process_inputs() - Componente para acessar APIs do FastAPI e interagir com a DB",
        "tags": [
          "FastAPIClient-process_inputs"
        ]
      }
    ]
  },
  "CustomComponent-iJBo4": {
    "input": "",
    "tools_metadata": [
      {
        "name": "ActionSelector-process_inputs",
        "description": "process_inputs() - Componente para selecionar a ação a ser executada baseado no contexto da conversa",
        "tags": [
          "ActionSelector-process_inputs"
        ]
      }
    ]
  },
  "Agent-tIIK7": {
    "add_current_date_tool": True,
    "agent_description": "A helpful assistant with access to the following tools:",
    "agent_llm": "OpenAI",
    "api_key": "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",
    "handle_parsing_errors": True,
    "input_value": "",
    "json_mode": False,
    "max_iterations": 15,
    "max_retries": 5,
    "max_tokens": None,
    "model_kwargs": {},
    "model_name": "gpt-4o-mini",
    "n_messages": 100,
    "openai_api_base": "",
    "order": "Ascending",
    "seed": 1,
    "sender": "Machine and User",
    "sender_name": "",
    "session_id": "",
    "system_prompt": "# Instruções para o AIAgent - Gerenciador de Negociações OLX\n\n## Visão Geral\nVocê é um agente especializado em gerenciar negociações de pranchas de surf no OLX. Você tem acesso a três ferramentas principais que devem ser utilizadas em conjunto para gerenciar as conversas e mensagens.\n\n## Ferramentas Disponíveis\n\n### 1. GetEnvVar\n- **Propósito**: Obter credenciais e configurações do arquivo .env\n- **Uso Inicial**: \n  - Primeiro, você DEVE usar esta ferramenta para obter o email do usuário\n  - Diretório: `C:\\Users\\pedro\\programas\\Olx-SurfBoards-Negotiator`\n  - Variável: `OLX_USERNAME`\n  - Este email será usado em todas as chamadas do FastAPIClient\n\n### 2. ActionSelector\n- **Propósito**: Determinar qual ação deve ser executada baseado no contexto\n- **Ações Possíveis**:\n  - `buscar_mensagens`: Buscar histórico de mensagens\n  - `enviar_mensagem`: Enviar uma nova mensagem\n- **Uso**:\n  - Use esta ferramenta antes de qualquer interação com o FastAPIClient\n  - Forneça o contexto da conversa ou instrução clara\n  - A ferramenta retornará a ação apropriada baseada em palavras-chave:\n    - Para buscar: \"buscar\", \"procurar\", \"encontrar\", \"listar\", \"ver\", \"mostrar\"\n    - Para enviar: \"enviar\", \"mandar\", \"responder\", \"resposta\", \"mensagem\"\n\n### 3. FastAPIClient\n- **Propósito**: Executar ações na API\n- **Parâmetros**:\n  - `acao`: Ação a ser executada (vem do ActionSelector)\n  - `email`: Email do usuário (vem do GetEnvVar)\n  - `anuncio_id`: ID do anúncio (quando necessário)\n  - `mensagem`: Texto da mensagem (quando necessário)\n  - `tipo`: Tipo da mensagem (\"recebida\" ou \"enviada\")\n  - `conversa_id`: ID da conversa (opcional, para filtrar mensagens)\n  - `respondida`: Status de resposta (opcional, para filtrar mensagens)\n- **Fluxo de Uso**:\n  1. Obter email do GetEnvVar\n  2. Usar ActionSelector para determinar a ação\n  3. Executar a ação via FastAPIClient\n\n## Fluxo de Trabalho\n\n1. **Inicialização**:\n   - Use GetEnvVar para obter o OLX_USERNAME\n   - Guarde este email para uso posterior\n\n2. **Ciclo de Trabalho**:\n   - Use ActionSelector para determinar a próxima ação\n   - Execute a ação via FastAPIClient\n   - Processe a resposta\n   - Repita o ciclo\n\n3. **Regras de Validação**:\n   - Sempre verifique se o email foi obtido antes de usar o FastAPIClient\n   - Use o ActionSelector antes de cada chamada ao FastAPIClient\n   - Verifique as respostas da API para garantir sucesso das operações\n\n## Exemplos de Uso\n\n1. **Buscar Mensagens**:\n   ```python\n   # 1. Obter email\n   email = GetEnvVar(env_var_name=\"OLX_USERNAME\", env_dir=\"C:\\\\Users\\\\pedro\\\\programas\\\\Olx-SurfBoards-Negotiator\")\n   \n   # 2. Determinar ação\n   acao = ActionSelector(input=\"buscar mensagens não respondidas\")\n   \n   # 3. Executar ação\n   resultado = FastAPIClient(\n       acao=\"buscar_mensagens\",\n       email=email,\n       respondida=\"False\"\n   )\n   ```\n\n2. **Enviar Mensagem**:\n   ```python\n   # 1. Determinar ação\n   acao = ActionSelector(input=\"enviar mensagem para o anúncio 123\")\n   \n   # 2. Executar ação\n   resultado = FastAPIClient(\n       acao=\"enviar_mensagem\",\n       email=email,\n       anuncio_id=\"123\",\n       mensagem=\"Olá, gostaria de saber mais sobre a prancha\"\n   )\n   ```\n\n## Tratamento de Erros\n- Se o GetEnvVar falhar, não prossiga com outras operações\n- Se o ActionSelector retornar uma ação inválida, use \"buscar_mensagens\" como fallback\n- Se o FastAPIClient retornar erro, tente novamente ou mude a ação\n\n## Prioridades\n1. Manter o email do usuário sempre atualizado\n2. Usar o ActionSelector para cada decisão\n3. Executar ações via FastAPIClient de forma ordenada\n4. Tratar erros adequadamente",
    "temperature": 0.1,
    "template": "{sender_name}: {text}",
    "timeout": 700,
    "verbose": True
  },
  "ChatInput-g5RAZ": {
    "files": "",
    "background_color": "",
    "chat_icon": "",
    "input_value": "",
    "sender": "User",
    "sender_name": "User",
    "session_id": "",
    "should_store_message": True,
    "text_color": ""
  }
}

def run_flow(message: str,
  endpoint: str,
  output_type: str = "chat",
  input_type: str = "chat",
  tweaks: Optional[dict] = None,
  api_key: Optional[str] = None) -> dict:
    """
    Run a flow with a given message and optional tweaks.

    :param message: The message to send to the flow
    :param endpoint: The ID or the endpoint name of the flow
    :param tweaks: Optional tweaks to customize the flow
    :return: The JSON response from the flow
    """
    api_url = f"{BASE_API_URL}/api/v1/run/{endpoint}"

    payload = {
        
        "output_type": output_type,
        "input_type": input_type,
    }
    headers = None
    if tweaks:
        payload["tweaks"] = tweaks
    if api_key:
        headers = {"x-api-key": api_key}
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="""Run a flow with a given message and optional tweaks.
Run it like: python <your file>.py "your message here" --endpoint "your_endpoint" --tweaks '{"key": "value"}'""",
        formatter_class=RawTextHelpFormatter)
    parser.add_argument("message", type=str, help="The message to send to the flow")
    parser.add_argument("--endpoint", type=str, default=ENDPOINT or FLOW_ID, help="The ID or the endpoint name of the flow")
    parser.add_argument("--tweaks", type=str, help="JSON string representing the tweaks to customize the flow", default=json.dumps(TWEAKS))
    parser.add_argument("--api_key", type=str, help="API key for authentication", default=None)
    parser.add_argument("--output_type", type=str, default="chat", help="The output type")
    parser.add_argument("--input_type", type=str, default="chat", help="The input type")
    parser.add_argument("--upload_file", type=str, help="Path to the file to upload", default=None)
    parser.add_argument("--components", type=str, help="Components to upload the file to", default=None)

    args = parser.parse_args()
    try:
      tweaks = json.loads(args.tweaks)
    except json.JSONDecodeError:
      raise ValueError("Invalid tweaks JSON string")

    if args.upload_file:
        if not upload_file:
            raise ImportError("Langflow is not installed. Please install it to use the upload_file function.")
        elif not args.components:
            raise ValueError("You need to provide the components to upload the file to.")
        tweaks = upload_file(file_path=args.upload_file, host=BASE_API_URL, flow_id=args.endpoint, components=[args.components], tweaks=tweaks)

    response = run_flow(
        message=args.message,
        endpoint=args.endpoint,
        output_type=args.output_type,
        input_type=args.input_type,
        tweaks=tweaks,
        api_key=args.api_key
    )

    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main()
