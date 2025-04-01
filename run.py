import os
import sys
import argparse
from Database.server import iniciar_servidor
from Database.visualizar_db import visualizar_banco
from OlxManager.scraper import main as scraper_main

def run_database():
    """Função para executar o servidor FastAPI"""
    print("Iniciando servidor FastAPI...")
    iniciar_servidor()

def run_visualizer():
    """Função para executar o visualizador do banco de dados"""
    print("Iniciando visualizador do banco de dados...")
    visualizar_banco()

def run_scraper():
    """Função para executar o scraper do OLX"""
    print("Iniciando scraper do OLX...")
    scraper_main()

def main():
    # Configuração do parser de argumentos
    parser = argparse.ArgumentParser(description='Executa os serviços da aplicação')
    parser.add_argument('--db', action='store_true', help='Executa o servidor de banco de dados')
    parser.add_argument('--showdb', action='store_true', help='Visualiza o conteúdo do banco de dados')
    parser.add_argument('--scraper', action='store_true', help='Executa o scraper do OLX')
    
    args = parser.parse_args()
    
    try:
        if args.db:
            run_database()
        elif args.showdb:
            run_visualizer()
        elif args.scraper:
            run_scraper()
        else:
            print("Por favor, especifique qual serviço deseja executar:")
            print("  --db       : Para executar o servidor de banco de dados")
            print("  --showdb   : Para visualizar o conteúdo do banco de dados")
            print("  --scraper  : Para executar o scraper do OLX")
            
    except KeyboardInterrupt:
        print("Aplicação encerrada pelo usuário")
    except Exception as e:
        print(f"Erro ao executar a aplicação: {e}")
        raise

if __name__ == "__main__":
    main() 