from langflow.base.prompts.api_utils import process_prompt_template
from langflow.custom import Component
from langflow.inputs.inputs import DefaultPromptField
from langflow.io import MessageTextInput, Output, PromptInput
from langflow.schema.message import Message
from langflow.template.utils import update_template_values
from typing import Optional


class PromptComponent(Component):
    display_name: str = "Prompt"
    description: str = "Create a prompt template with dynamic variables."
    icon = "prompts"
    trace_type = "prompt"
    name = "Prompt"

    inputs = [
        PromptInput(name="template", display_name="Template"),
        MessageTextInput(
            name="chat_input",
            display_name="Chat Input",
            info="Input da mensagem do chat para processamento",
        ),
        MessageTextInput(
            name="tool_placeholder",
            display_name="Tool Placeholder",
            tool_mode=True,
            advanced=True,
            info="A placeholder input for tool mode.",
        ),
    ]

    outputs = [
        Output(display_name="Prompt Message", name="prompt", method="build_prompt"),
    ]

    async def build_prompt(self) -> Message:
        # Obtém o input do chat
        chat_input = self._attributes.get("chat_input", "")
        
        # Formata o prompt com o input do chat
        prompt = NegotiationPrompt.format_prompt(
            conversation_history="",  # Será preenchido pelo histórico
            product_info={},  # Será preenchido com informações do produto
            market_data={},  # Será preenchido com dados de mercado
            input_message=chat_input
        )
        
        # Cria a mensagem do prompt com um template válido
        prompt_message = Message(
            text=prompt,
            template="Você é um agente especializado em negociações. {input_message}"
        )
        
        self.status = prompt_message.text
        return prompt_message

    def _update_template(self, frontend_node: dict):
        prompt_template = frontend_node["template"]["template"]["value"]
        custom_fields = frontend_node["custom_fields"]
        frontend_node_template = frontend_node["template"]
        _ = process_prompt_template(
            template=prompt_template,
            name="template",
            custom_fields=custom_fields,
            frontend_node_template=frontend_node_template,
        )
        return frontend_node

    async def update_frontend_node(self, new_frontend_node: dict, current_frontend_node: dict):
        """This function is called after the code validation is done."""
        frontend_node = await super().update_frontend_node(new_frontend_node, current_frontend_node)
        template = frontend_node["template"]["template"]["value"]
        # Kept it duplicated for backwards compatibility
        _ = process_prompt_template(
            template=template,
            name="template",
            custom_fields=frontend_node["custom_fields"],
            frontend_node_template=frontend_node["template"],
        )
        # Now that template is updated, we need to grab any values that were set in the current_frontend_node
        # and update the frontend_node with those values
        update_template_values(new_template=frontend_node, previous_template=current_frontend_node["template"])
        return frontend_node

    def _get_fallback_input(self, **kwargs):
        return DefaultPromptField(**kwargs)


class NegotiationPrompt:
    @staticmethod
    def get_prompt(
        conversation_history: str,
        product_info: Optional[dict] = None,
        market_data: Optional[dict] = None
    ) -> str:
        base_prompt = """Você é um agente especializado em gerenciar negociações de pranchas de surf no OLX. Você tem acesso a três ferramentas principais que devem ser utilizadas em conjunto para gerenciar as conversas e mensagens.

FERRAMENTAS DISPONÍVEIS:

1. GetEnvVar:
- Obter credenciais e configurações do arquivo .env
- Diretório: C:\\Users\\pedro\\programas\\Olx-SurfBoards-Negotiator
- Variável: OLX_USERNAME
- Use esta ferramenta primeiro para obter o email do usuário

2. ActionSelector:
- Determinar qual ação executar baseado no contexto
- Ações possíveis:
  * buscar_mensagens: Buscar histórico de mensagens
  * enviar_mensagem: Enviar uma nova mensagem
- Use antes de qualquer interação com o FastAPIClient
- IMPORTANTE: Após consultar o histórico de mensagens e formular uma resposta, SEMPRE use a ação "enviar_mensagem" para responder ao vendedor

3. FastAPIClient:
- Executar ações na API
- Parâmetros necessários:
  * acao: Ação a executar (do ActionSelector)
  * email: Email do usuário (do GetEnvVar)
  * anuncio_id: ID do anúncio (quando necessário)
  * mensagem: Texto da mensagem (quando necessário)
  * tipo: Tipo da mensagem ("recebida" ou "enviada")

CONTEXTO BÁSICO:
- Produto: {product_type}
- Preço Anunciado: {listed_price}€
- Seu Preço Máximo: {max_price}€

ESTRATÉGIAS DE NEGOCIAÇÃO:

1. ABORDAGEM INICIAL:
- Cumprimente o vendedor pelo nome (se disponível)
- Demonstre interesse genuíno pelo produto
- Faça perguntas relevantes sobre o item
- Mantenha tom cordial e profissional

2. TÉCNICAS DE NEGOCIAÇÃO:
- Primeira oferta: 70-80% do preço anunciado
- Justifique sua oferta de forma educada
- Ofereça facilidades como pagamento em dinheiro e retirada imediata
- Mantenha flexibilidade para contra-propostas

3. COMUNICAÇÃO:
- Seja sempre educado e profissional
- Evite ofertas extremamente baixas
- Não desvalorize o produto
- Mantenha equilíbrio entre interesse e desprendimento

4. LIMITES:
- Nunca ultrapasse o preço máximo definido
- Não use informações falsas
- Respeite quando o vendedor indicar preço fixo

FLUXO DE TRABALHO:
1. Inicialização:
   - Use GetEnvVar para obter o OLX_USERNAME
   - Guarde este email para uso posterior

2. Ciclo de Trabalho:
   - Use ActionSelector para determinar a próxima ação
   - Execute a ação via FastAPIClient
   - Processe a resposta
   - Repita o ciclo

3. Regras de Validação:
   - Sempre verifique se o email foi obtido antes de usar o FastAPIClient
   - Use o ActionSelector antes de cada chamada ao FastAPIClient
   - Verifique as respostas da API para garantir sucesso das operações

4. Processo de Resposta:
   - Primeiro use "buscar_mensagens" para obter o histórico atual
   - Analise o histórico para entender o contexto
   - Formule sua resposta
   - Use "enviar_mensagem" para enviar sua resposta
   - Inclua o ID do anúncio e a mensagem formatada

HISTÓRICO DA CONVERSA:
{conversation_history}

MENSAGEM PENDENTE PARA RESPOSTA:
{input_message}

DIRETRIZES PARA RESPOSTA:
1. Analise o contexto atual da conversa
2. Escolha a estratégia mais adequada
3. Formule uma resposta que:
   - Seja educada e profissional
   - Inclua argumentos relevantes
   - Mantenha a negociação progredindo
   - Respeite as diretrizes acima
4. Use o ActionSelector com "enviar_mensagem" para enviar sua resposta

TRATAMENTO DE ERROS:
- Se o GetEnvVar falhar, não prossiga com outras operações
- Se o ActionSelector retornar uma ação inválida, use "buscar_mensagens" como fallback
- Se o FastAPIClient retornar erro, tente novamente ou mude a ação

IMPORTANTE: Sua resposta deve ser apenas a mensagem que será enviada ao vendedor, sem incluir explicações ou formatação adicional. Não inclua marcadores como "Mensagem:" ou "Aqui está o que foi enviado:". Apenas o texto da mensagem.

Responda de forma natural, como se fosse um comprador real, mantendo o tom cordial e profissional. Use o histórico da conversa para adaptar suas estratégias de negociação.
"""
        return base_prompt

    @staticmethod
    def format_prompt(
        conversation_history: str,
        product_info: dict,
        market_data: dict,
        input_message: str
    ) -> str:
        """
        Formata o prompt com as informações básicas do produto.
        
        Args:
            conversation_history (str): Histórico da conversa
            product_info (dict): Informações básicas do produto
            market_data (dict): Dados básicos de mercado
            input_message (str): Mensagem pendente para resposta
            
        Returns:
            str: Prompt formatado
        """
        prompt = NegotiationPrompt.get_prompt(
            conversation_history=conversation_history,
            product_info=product_info,
            market_data=market_data
        )
        
        # Substitui os placeholders com dados básicos
        formatted_prompt = prompt.format(
            product_type=product_info.get('type', 'produto'),
            listed_price=product_info.get('price', '0'),
            max_price=market_data.get('max_price', '0'),
            conversation_history=conversation_history,
            input_message=input_message
        )
        
        return formatted_prompt
 