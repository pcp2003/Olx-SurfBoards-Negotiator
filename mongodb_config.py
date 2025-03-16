import os
from dotenv import load_dotenv

load_dotenv()

# Configurações do MongoDB
MONGODB_CONFIG = {
    'local': {
        'uri': 'mongodb://localhost:27017/',
        'db_name': 'olx_negotiator'
    },
    'atlas': {
        'uri': os.getenv('MONGODB_URI', 'mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/'),
        'db_name': 'olx_negotiator'
    }
}

# Configuração atual (mude para 'atlas' se quiser usar MongoDB Atlas)
CURRENT_CONFIG = 'local' 