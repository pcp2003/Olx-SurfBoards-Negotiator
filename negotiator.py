from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import os
from dotenv import load_dotenv
from database import Database
import random

load_dotenv()

class SurfNegotiator:
    
    def __init__(self):
        self.db = Database()
        # Usa a conta do arquivo .env
        self.account_username = os.getenv("OLX_USERNAME")
        if not self.account_username:
            raise ValueError("OLX_USERNAME não encontrado no arquivo .env")
            
        self.account_id = self.db.get_account_id(self.account_username)
        if not self.account_id:
            self.account_id = self.db.add_account(self.account_username)
        
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Carrega estratégias bem-sucedidas de outras contas
        self.successful_strategies = self.db.get_successful_strategies()
        
        # Template para o prompt de negociação
        self.negotiation_prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um negociador especializado em pranchas de surf.
            Seu objetivo é negociar o melhor preço possível, mantendo um tom profissional e amigável.
            Você tem um orçamento máximo de {max_budget}€.
            O preço inicial do produto é {initial_price}€.
            
            Regras de negociação:
            1. Comece com uma oferta 20% abaixo do preço inicial
            2. Não ultrapasse seu orçamento máximo
            3. Seja paciente e profissional
            4. Faça contra-ofertas gradualmente
            5. Se o vendedor não aceitar, agradeça e encerre a conversa
            
            Estratégias disponíveis:
            {available_strategies}
            
            IMPORTANTE: Mantenha um tom natural e não mencione outras negociações.
            Cada conversa deve parecer única e independente.
            """),
            ("human", "{input}")
        ])
        
        # Template para análise de sentimento
        self.sentiment_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analise o sentimento da mensagem do vendedor.
            Responda apenas com uma das seguintes opções:
            - POSITIVE: se o vendedor está aberto à negociação
            - NEGATIVE: se o vendedor está fechado à negociação
            - NEUTRAL: se não é possível determinar
            """),
            ("human", "{input}")
        ])

    def get_random_strategy(self):
        """Retorna uma estratégia aleatória das bem-sucedidas"""
        if not self.successful_strategies:
            return "standard_negotiation"
        
        # Escolhe aleatoriamente uma estratégia bem-sucedida
        strategy = random.choice(self.successful_strategies)
        return strategy[0]  # Retorna o tipo da estratégia

    def analyze_sentiment(self, message):
        """Analisa o sentimento da mensagem do vendedor"""
        chain = self.sentiment_prompt | self.llm
        response = chain.invoke({"input": message})
        return response.content.strip()

    def generate_response(self, conversation_id, message):
        """Gera uma resposta para a mensagem do vendedor"""
        # Busca informações da conversa
        conversation_data = self.db.get_conversation(conversation_id, self.account_id)
        if not conversation_data:
            return "Desculpe, não encontrei informações sobre esta conversa."

        conversation = conversation_data['conversation']
        messages = conversation_data['messages']
        
        # Prepara o contexto da conversa
        conversation_history = "\n".join([
            f"{msg[2]}: {msg[3]}" for msg in messages
        ])
        
        # Escolhe uma estratégia aleatória
        strategy = self.get_random_strategy()
        
        # Gera a resposta
        chain = self.negotiation_prompt | self.llm
        response = chain.invoke({
            "input": f"Histórico da conversa:\n{conversation_history}\n\nÚltima mensagem do vendedor: {message}",
            "max_budget": 300,  # Ajuste conforme necessário
            "initial_price": conversation[4],
            "available_strategies": f"Estratégia atual: {strategy}"
        })
        
        return response.content.strip()

    def process_message(self, conversation_id, sender, message):
        """Processa uma nova mensagem e gera uma resposta"""
        # Salva a mensagem do vendedor
        self.db.add_message(conversation_id, sender, message)
        
        # Analisa o sentimento
        sentiment = self.analyze_sentiment(message)
        
        # Se o sentimento for negativo, encerra a conversa
        if sentiment == "NEGATIVE":
            self.db.update_conversation_status(conversation_id, "closed")
            return "Obrigado pelo seu tempo. Infelizmente não conseguimos chegar a um acordo."
        
        # Gera e salva a resposta
        response = self.generate_response(conversation_id, message)
        self.db.add_message(conversation_id, "buyer", response)
        
        # Registra o sucesso da estratégia se a resposta for positiva
        if sentiment == "POSITIVE":
            strategy = self.get_random_strategy()
            self.db.add_strategy(self.account_id, strategy, 0.8)
        
        return response

    def update_conversation_status(self, conversation_id, status):
        """Atualiza o status de uma conversa"""
        self.db.update_conversation_status(conversation_id, status) 