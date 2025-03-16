import sqlite3
from datetime import datetime
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, db_name="surf_negotiations.db"):
        self.db_name = db_name
        # Usa a conta do arquivo .env
        self.account_username = os.getenv("OLX_USERNAME")
        if not self.account_username:
            raise ValueError("OLX_USERNAME não encontrado no arquivo .env")
            
        self.account_id = self.get_account_id(self.account_username)
        if not self.account_id:
            self.account_id = self.add_account(self.account_username)
            
        self.init_db()

    def init_db(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Tabela de contas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            created_at TIMESTAMP,
            last_used TIMESTAMP,
            status TEXT
        )
        ''')

        # Tabela de conversas (agora com account_id)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            seller_hash TEXT,  # Hash do seller_id para anonimização
            product_title TEXT,
            product_price REAL,
            status TEXT,
            created_at TIMESTAMP,
            last_updated TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
        ''')

        # Tabela de mensagens
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            sender TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        ''')

        # Tabela de estratégias (para compartilhar conhecimento entre contas)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            strategy_type TEXT,
            success_rate REAL,
            created_at TIMESTAMP,
            last_used TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
        ''')

        conn.commit()
        conn.close()

    def add_account(self, username):
        """Adiciona uma nova conta"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now()
        cursor.execute('''
        INSERT INTO accounts (username, created_at, last_used, status)
        VALUES (?, ?, ?, ?)
        ''', (username, now, now, 'active'))
        
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return account_id

    def get_account_id(self, username):
        """Retorna o ID da conta pelo username"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM accounts WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None

    def hash_seller_id(self, seller_id):
        """Gera um hash anônimo do seller_id"""
        return hashlib.sha256(seller_id.encode()).hexdigest()

    def add_conversation(self, seller_id, product_title, product_price):
        """Adiciona uma nova conversa"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        seller_hash = self.hash_seller_id(seller_id)
        now = datetime.now()
        
        cursor.execute('''
        INSERT INTO conversations (account_id, seller_hash, product_title, product_price, status, created_at, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (self.account_id, seller_hash, product_title, product_price, 'active', now, now))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conversation_id

    def add_message(self, conversation_id, sender, content):
        """Adiciona uma nova mensagem"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now()
        cursor.execute('''
        INSERT INTO messages (conversation_id, sender, content, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (conversation_id, sender, content, now))
        
        # Atualiza o last_updated da conversa
        cursor.execute('''
        UPDATE conversations SET last_updated = ? WHERE id = ?
        ''', (now, conversation_id))
        
        conn.commit()
        conn.close()

    def get_conversation(self, conversation_id):
        """Retorna uma conversa e suas mensagens (apenas para a conta específica)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Verifica se a conversa pertence à conta
        cursor.execute('''
        SELECT * FROM conversations 
        WHERE id = ? AND account_id = ?
        ''', (conversation_id, self.account_id))
        conversation = cursor.fetchone()
        
        if conversation:
            cursor.execute('''
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY timestamp
            ''', (conversation_id,))
            messages = cursor.fetchall()
            
            return {
                'conversation': conversation,
                'messages': messages
            }
        
        conn.close()
        return None

    def get_active_conversations(self):
        """Retorna todas as conversas ativas da conta específica"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM conversations 
        WHERE account_id = ? AND status = 'active' 
        ORDER BY last_updated DESC
        ''', (self.account_id,))
        conversations = cursor.fetchall()
        
        conn.close()
        return conversations

    def add_strategy(self, strategy_type, success_rate):
        """Adiciona uma nova estratégia de negociação"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now()
        cursor.execute('''
        INSERT INTO strategies (account_id, strategy_type, success_rate, created_at, last_used)
        VALUES (?, ?, ?, ?, ?)
        ''', (self.account_id, strategy_type, success_rate, now, now))
        
        conn.commit()
        conn.close()

    def get_successful_strategies(self, min_success_rate=0.7):
        """Retorna estratégias bem-sucedidas de todas as contas"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT strategy_type, AVG(success_rate) as avg_success_rate
        FROM strategies
        WHERE success_rate >= ?
        GROUP BY strategy_type
        ORDER BY avg_success_rate DESC
        ''', (min_success_rate,))
        
        strategies = cursor.fetchall()
        conn.close()
        return strategies

    def update_conversation_status(self, conversation_id, status):
        """Atualiza o status de uma conversa"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE conversations 
        SET status = ?, last_updated = ?
        WHERE id = ? AND account_id = ?
        ''', (status, datetime.now(), conversation_id, self.account_id))
        
        conn.commit()
        conn.close() 