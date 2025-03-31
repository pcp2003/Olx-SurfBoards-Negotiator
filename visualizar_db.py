import sqlite3
import json
from datetime import datetime

def visualizar_banco():
    """Visualiza o conteúdo do banco de dados"""
    try:
        # Conecta ao banco
        conn = sqlite3.connect("mensagens.db")
        conn.row_factory = sqlite3.Row  # Permite acessar resultados por nome de coluna
        cursor = conn.cursor()

        # Visualiza conversas
        print("\n" + "="*100)
        print("📬 CONVERSAS E MENSAGENS".center(100))
        print("="*100)

        cursor.execute("SELECT * FROM conversas")
        conversas = cursor.fetchall()
        
        if not conversas:
            print("\nNenhuma conversa encontrada no banco de dados.")
        else:
            for conversa in conversas:
                print("\n" + "="*100)
                print(f"📝 CONVERSA #{conversa['id']}")
                print(f"📧 Email: {conversa['email']}")
                print(f"🔗 Anúncio ID: {conversa['anuncio_id']}")
                
                # Informações do anúncio
                if conversa['titulo_anuncio']:
                    print(f"📋 Título: {conversa['titulo_anuncio']}")
                if conversa['nome_vendedor']:
                    print(f"👤 Vendedor: {conversa['nome_vendedor']}")
                if conversa['preco_anuncio']:
                    print(f"💰 Preço: {conversa['preco_anuncio']}")
                print("="*100)

                # Busca mensagens desta conversa
                cursor.execute("SELECT * FROM mensagens WHERE conversa_id = ? ORDER BY id", (conversa['id'],))
                mensagens = cursor.fetchall()
                
                if mensagens:
                    print("\n💬 HISTÓRICO DE MENSAGENS:")
                    print("-"*100)
                    for msg in mensagens:
                        tipo_emoji = "📤" if msg['tipo'] == 'enviada' else "📥"
                        status_emoji = "✅" if msg['respondida'] else "⏳"
                        print(f"\n{tipo_emoji} {msg['tipo'].upper()} {status_emoji}")
                        print(f"   ID: {msg['id']}")
                        print(f"   Mensagem: {msg['mensagem']}")
                        print("-"*50)
                else:
                    print("\n💬 Nenhuma mensagem encontrada nesta conversa")

        print("\n" + "="*100)
        print("FIM DA VISUALIZAÇÃO".center(100))
        print("="*100 + "\n")

        conn.close()

    except Exception as e:
        print(f"\n❌ Erro ao visualizar banco: {e}")

if __name__ == "__main__":
    visualizar_banco() 