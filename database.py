import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import hashlib
import logging
from mongodb_config import MONGODB_CONFIG, CURRENT_CONFIG

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Inicializa a conexão com o MongoDB"""
        load_dotenv()
        self.username = os.getenv("OLX_USERNAME")
        if not self.username:
            raise ValueError("OLX_USERNAME não encontrado no arquivo .env")
            
        # Obtém a configuração atual
        config = MONGODB_CONFIG[CURRENT_CONFIG]
        
        try:
            # Conecta ao MongoDB
            self.client = MongoClient(config['uri'])
            self.db = self.client[config['db_name']]
            
            # Testa a conexão
            self.client.server_info()
            logger.info(f"Conectado ao MongoDB com sucesso usando configuração: {CURRENT_CONFIG}")
            
            # Obtém ou cria o ID da conta
            self.account_id = self.get_account_id(self.username)
            if not self.account_id:
                self.account_id = self.add_account(self.username)
                
        except Exception as e:
            logger.error(f"Erro ao conectar ao MongoDB: {e}")
            raise

    def add_account(self, username):
        """Adiciona uma nova conta ao banco de dados"""
        try:
            account = {
                'username': username,
                'created_at': datetime.now(),
                'last_used': datetime.now(),
                'status': 'active'
            }
            result = self.db.accounts.insert_one(account)
            logger.info(f"Conta {username} criada com sucesso")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao criar conta: {e}")
            return None

    def get_account_id(self, username):
        """Obtém o ID de uma conta existente"""
        try:
            account = self.db.accounts.find_one({'username': username})
            if account:
                return str(account['_id'])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar conta: {e}")
            return None

    def hash_seller_id(self, seller_id):
        """Gera um hash para o ID do vendedor"""
        return hashlib.sha256(seller_id.encode()).hexdigest()

    def add_conversation(self, seller_id, product_title, product_price):
        """Adiciona uma nova conversa ao banco de dados"""
        try:
            conversation = {
                'account_id': self.account_id,
                'seller_hash': self.hash_seller_id(seller_id),
                'product_title': product_title,
                'product_price': product_price,
                'created_at': datetime.now(),
                'last_message_at': datetime.now(),
                'status': 'active'
            }
            result = self.db.conversations.insert_one(conversation)
            logger.info(f"Conversa criada com sucesso para o produto: {product_title}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao criar conversa: {e}")
            return None

    def add_message(self, conversation_id, sender, message):
        """Adiciona uma nova mensagem à conversa"""
        try:
            message_doc = {
                'conversation_id': conversation_id,
                'sender': sender,
                'message': message,
                'timestamp': datetime.now()
            }
            result = self.db.messages.insert_one(message_doc)
            
            # Atualiza o timestamp da última mensagem na conversa
            self.db.conversations.update_one(
                {'_id': conversation_id},
                {'$set': {'last_message_at': datetime.now()}}
            )
            
            logger.info(f"Mensagem adicionada com sucesso na conversa {conversation_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem: {e}")
            return None

    def get_conversation(self, conversation_id):
        """Obtém uma conversa específica"""
        try:
            conversation = self.db.conversations.find_one({'_id': conversation_id})
            if conversation:
                # Converte ObjectId para string
                conversation['_id'] = str(conversation['_id'])
                return conversation
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar conversa: {e}")
            return None

    def get_active_conversations(self):
        """Obtém todas as conversas ativas da conta"""
        try:
            conversations = list(self.db.conversations.find({
                'account_id': self.account_id,
                'status': 'active'
            }))
            
            # Converte ObjectIds para strings
            for conv in conversations:
                conv['_id'] = str(conv['_id'])
                
            return conversations
        except Exception as e:
            logger.error(f"Erro ao buscar conversas ativas: {e}")
            return []

    def add_strategy(self, strategy_name, success_rate):
        """Adiciona uma nova estratégia de negociação"""
        try:
            strategy = {
                'account_id': self.account_id,
                'name': strategy_name,
                'success_rate': success_rate,
                'created_at': datetime.now(),
                'last_used': datetime.now()
            }
            result = self.db.strategies.insert_one(strategy)
            logger.info(f"Estratégia {strategy_name} adicionada com sucesso")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao adicionar estratégia: {e}")
            return None

    def get_successful_strategies(self):
        """Obtém todas as estratégias bem-sucedidas da conta"""
        try:
            strategies = list(self.db.strategies.find({
                'account_id': self.account_id,
                'success_rate': {'$gte': 0.7}
            }))
            
            # Converte ObjectIds para strings
            for strat in strategies:
                strat['_id'] = str(strat['_id'])
                
            return [(strat['name'], strat['success_rate']) for strat in strategies]
        except Exception as e:
            logger.error(f"Erro ao buscar estratégias: {e}")
            return [] 