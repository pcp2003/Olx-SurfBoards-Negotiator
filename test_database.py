import unittest
from unittest.mock import Mock, patch
from pymongo import MongoClient
from database import Database
import os
from datetime import datetime
from bson import ObjectId

class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        
        """Configuração inicial para todos os testes"""

        # Configuração do MongoDB
        cls.mongo_uri = "mongodb://localhost:27017/"
        cls.test_db_name = "olx_negotiator_test"
        
        # Conecta ao MongoDB
        cls.client = MongoClient(cls.mongo_uri)
        cls.test_db = cls.client[cls.test_db_name]
        
        # Mock do arquivo .env
        with patch.dict(os.environ, {'OLX_USERNAME': 'test@email.com'}):
            cls.db = Database()
            cls.db.db = cls.test_db

    def setUp(self):
        """Configuração antes de cada teste"""
        # Limpa as coleções antes de cada teste
        self.test_db.accounts.delete_many({})
        self.test_db.conversations.delete_many({})
        self.test_db.messages.delete_many({})
        self.test_db.strategies.delete_many({})

    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        # Remove o banco de dados de teste
        cls.client.drop_database(cls.test_db_name)
        cls.client.close()

    def test_connection(self):
        """Testa a conexão com o MongoDB"""
        try:
            # Tenta executar um comando simples
            self.client.server_info()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Falha na conexão com MongoDB: {e}")

    def test_init(self):
        """Testa a inicialização do banco de dados"""
        self.assertIsNotNone(self.db.client)
        self.assertIsNotNone(self.db.db)
        self.assertIsNotNone(self.db.account_id)
        self.assertEqual(self.db.username, "test@email.com")

    def test_add_account(self):
        """Testa a adição de uma nova conta"""
        # Testa adição de conta
        account_id = self.db.add_account("test@email.com")
        self.assertIsNotNone(account_id)
        
        # Verifica se a conta foi criada
        account = self.test_db.accounts.find_one({'username': "test@email.com"})
        self.assertIsNotNone(account)
        self.assertEqual(account['username'], "test@email.com")
        self.assertEqual(account['status'], "active")
        
        # Testa duplicidade
        duplicate_id = self.db.add_account("test@email.com")
        self.assertIsNotNone(duplicate_id)
        self.assertEqual(duplicate_id, account_id)

    def test_get_account_id(self):
        """Testa a obtenção do ID de uma conta"""
        # Cria uma conta de teste
        account = {
            'username': "test@email.com",
            'created_at': datetime.now(),
            'last_used': datetime.now(),
            'status': 'active'
        }
        result = self.test_db.accounts.insert_one(account)
        
        # Obtém o ID
        account_id = self.db.get_account_id("test@email.com")
        self.assertEqual(account_id, str(result.inserted_id))
        
        # Testa conta inexistente
        nonexistent_id = self.db.get_account_id("nonexistent@email.com")
        self.assertIsNone(nonexistent_id)

    def test_hash_seller_id(self):
        """Testa a geração de hash para ID do vendedor"""
        seller_id = "vendedor123"
        hash1 = self.db.hash_seller_id(seller_id)
        hash2 = self.db.hash_seller_id(seller_id)
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, seller_id)
        self.assertEqual(len(hash1), 64)  # SHA-256 gera 64 caracteres hexadecimais

    def test_add_conversation(self):
        """Testa a adição de uma nova conversa"""
        seller_id = "vendedor123"
        product_title = "Prancha de Surf"
        product_price = 500.0
        
        conversation_id = self.db.add_conversation(seller_id, product_title, product_price)
        self.assertIsNotNone(conversation_id)
        
        # Verifica se a conversa foi criada
        conversation = self.test_db.conversations.find_one({'_id': ObjectId(conversation_id)})
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation['seller_hash'], self.db.hash_seller_id(seller_id))
        self.assertEqual(conversation['product_title'], product_title)
        self.assertEqual(conversation['product_price'], product_price)
        self.assertEqual(conversation['status'], "active")

    def test_add_message(self):
        """Testa a adição de uma mensagem"""
        # Cria uma conversa primeiro
        conversation = {
            'account_id': self.db.account_id,
            'seller_hash': self.db.hash_seller_id("vendedor123"),
            'product_title': "Prancha",
            'product_price': 500.0,
            'created_at': datetime.now(),
            'last_message_at': datetime.now(),
            'status': 'active'
        }
        conv_result = self.test_db.conversations.insert_one(conversation)
        
        # Adiciona uma mensagem
        message_id = self.db.add_message(str(conv_result.inserted_id), "vendedor", "Olá, tudo bem?")
        self.assertIsNotNone(message_id)
        
        # Verifica se a mensagem foi adicionada
        message = self.test_db.messages.find_one({'_id': ObjectId(message_id)})
        self.assertIsNotNone(message)
        self.assertEqual(message['sender'], "vendedor")
        self.assertEqual(message['message'], "Olá, tudo bem?")
        
        # Verifica se o timestamp da conversa foi atualizado
        updated_conv = self.test_db.conversations.find_one({'_id': conv_result.inserted_id})
        self.assertGreater(updated_conv['last_message_at'], conversation['last_message_at'])

    def test_get_conversation(self):
        """Testa a obtenção de uma conversa"""
        # Cria uma conversa de teste
        conversation = {
            'account_id': self.db.account_id,
            'seller_hash': self.db.hash_seller_id("vendedor123"),
            'product_title': "Prancha de Surf",
            'product_price': 500.0,
            'created_at': datetime.now(),
            'last_message_at': datetime.now(),
            'status': 'active'
        }
        result = self.test_db.conversations.insert_one(conversation)
        
        # Obtém a conversa
        conv = self.db.get_conversation(str(result.inserted_id))
        self.assertIsNotNone(conv)
        self.assertEqual(conv['seller_hash'], self.db.hash_seller_id("vendedor123"))
        self.assertEqual(conv['product_title'], "Prancha de Surf")
        self.assertEqual(conv['product_price'], 500.0)
        
        # Testa conversa inexistente
        nonexistent_conv = self.db.get_conversation(str(ObjectId()))
        self.assertIsNone(nonexistent_conv)

    def test_get_active_conversations(self):
        """Testa a obtenção de conversas ativas"""
        # Cria algumas conversas
        conversations = [
            {
                'account_id': self.db.account_id,
                'seller_hash': self.db.hash_seller_id("vendedor1"),
                'product_title': "Prancha 1",
                'product_price': 500.0,
                'created_at': datetime.now(),
                'last_message_at': datetime.now(),
                'status': 'active'
            },
            {
                'account_id': self.db.account_id,
                'seller_hash': self.db.hash_seller_id("vendedor2"),
                'product_title': "Prancha 2",
                'product_price': 600.0,
                'created_at': datetime.now(),
                'last_message_at': datetime.now(),
                'status': 'active'
            },
            {
                'account_id': self.db.account_id,
                'seller_hash': self.db.hash_seller_id("vendedor3"),
                'product_title': "Prancha 3",
                'product_price': 700.0,
                'created_at': datetime.now(),
                'last_message_at': datetime.now(),
                'status': 'closed'
            }
        ]
        self.test_db.conversations.insert_many(conversations)
        
        # Obtém as conversas ativas
        active_convs = self.db.get_active_conversations()
        self.assertEqual(len(active_convs), 2)
        self.assertTrue(all(conv['status'] == 'active' for conv in active_convs))

    def test_add_strategy(self):
        """Testa a adição de uma estratégia"""
        strategy_name = "friendly"
        success_rate = 0.8
        
        strategy_id = self.db.add_strategy(strategy_name, success_rate)
        self.assertIsNotNone(strategy_id)
        
        # Verifica se a estratégia foi adicionada
        strategy = self.test_db.strategies.find_one({'_id': ObjectId(strategy_id)})
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy['name'], strategy_name)
        self.assertEqual(strategy['success_rate'], success_rate)
        self.assertEqual(strategy['account_id'], self.db.account_id)

    def test_get_successful_strategies(self):
        """Testa a obtenção de estratégias bem-sucedidas"""
        # Adiciona algumas estratégias
        strategies = [
            {
                'account_id': self.db.account_id,
                'name': "friendly",
                'success_rate': 0.8,
                'created_at': datetime.now(),
                'last_used': datetime.now()
            },
            {
                'account_id': self.db.account_id,
                'name': "aggressive",
                'success_rate': 0.7,
                'created_at': datetime.now(),
                'last_used': datetime.now()
            },
            {
                'account_id': self.db.account_id,
                'name': "professional",
                'success_rate': 0.6,
                'created_at': datetime.now(),
                'last_used': datetime.now()
            }
        ]
        self.test_db.strategies.insert_many(strategies)
        
        # Obtém as estratégias
        successful_strategies = self.db.get_successful_strategies()
        self.assertEqual(len(successful_strategies), 2)
        self.assertTrue(all(rate >= 0.7 for _, rate in successful_strategies))

if __name__ == '__main__':
    unittest.main() 