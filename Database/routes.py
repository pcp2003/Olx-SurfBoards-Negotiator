from fastapi import APIRouter, HTTPException
from .models import MensagemRequest
from .database import get_db, logger
import sqlite3

router = APIRouter()

@router.get("/conversas/pendentes")
def buscar_conversas_pendentes(email: str):
    """Retorna conversas com mensagens recebidas não respondidas"""
    try:
        with get_db() as conn:
            conversas = conn.execute(
                """
                SELECT c.id, c.email, c.anuncio_id, m.id, m.tipo, m.mensagem, m.respondida
                FROM conversas c
                JOIN mensagens m ON c.id = m.conversa_id
                WHERE c.email = ?
                AND m.tipo = 'recebida'
                AND m.respondida = FALSE
                ORDER BY c.id, m.id
                """,
                (email,),
            ).fetchall()

            resultado = {}
            for conv in conversas:
                if conv["id"] not in resultado:
                    resultado[conv["id"]] = {
                        "id": conv["id"],
                        "email": conv["email"],
                        "anuncio_id": conv["anuncio_id"],
                        "mensagens": [],
                    }
                resultado[conv["id"]]["mensagens"].append(
                    {
                        "id": conv["id"],
                        "conversa_id": conv["id"],
                        "tipo": conv["tipo"],
                        "mensagem": conv["mensagem"],
                        "respondida": bool(conv["respondida"]),
                    }
                )

            logger.info(f"Buscadas {len(resultado)} conversas pendentes na DB")
            return {"conversas_pendentes": list(resultado.values())}
    except Exception as e:
        logger.error(f"Erro ao buscar conversas pendentes na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar conversas")

@router.post("/criar-conversa")
def criar_conversa(email: str, anuncio_id: str):
    """Cria uma nova conversa no banco de dados"""
    try:
        with get_db() as conn:
            # Verifica se a conversa já existe
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM conversas 
                WHERE email = ? AND anuncio_id = ?
            """, (email, anuncio_id))
            
            if cursor.fetchone():
                logger.info(f"Conversa já existe para email {email} e anúncio {anuncio_id}")
                return {"message": "Conversa já existe"}
            
            # Cria nova conversa
            cursor.execute("""
                INSERT INTO conversas (email, anuncio_id)
                VALUES (?, ?)
            """, (email, anuncio_id))
            
            conn.commit()
            logger.info(f"Nova conversa criada para email {email} e anúncio {anuncio_id}")
            return {"message": "Conversa criada com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao criar conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enviar-mensagem")
def enviar_mensagem(email: str, anuncio_id: str, mensagem_data: MensagemRequest):
    """Registra uma mensagem enviada e marca todas as mensagens recebidas anteriores como respondidas"""
    try:
        with get_db() as conn:
            # Usa INSERT OR IGNORE para evitar duplicatas
            conn.execute(
                "INSERT OR IGNORE INTO conversas (email, anuncio_id) VALUES (?, ?)",
                (email, anuncio_id),
            )
            
            # Atualiza o updated_at da conversa
            conn.execute(
                "UPDATE conversas SET updated_at = CURRENT_TIMESTAMP WHERE email = ? AND anuncio_id = ?",
                (email, anuncio_id),
            )
            
            conversa = conn.execute(
                "SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?",
                (email, anuncio_id),
            ).fetchone()

            if not conversa:
                raise HTTPException(status_code=400, detail="Erro ao criar conversa")

            # Marca mensagens recebidas como respondidas em uma única query
            conn.execute(
                """
                UPDATE mensagens
                SET respondida = TRUE
                WHERE conversa_id = ?
                AND tipo = 'recebida'
                AND respondida = FALSE
                """,
                (conversa["id"],),
            )

            # Insere a nova mensagem
            conn.execute(
                """
                INSERT INTO mensagens (conversa_id, tipo, mensagem, respondida)
                VALUES (?, 'enviada', ?, FALSE)
                """,
                (conversa["id"], mensagem_data.mensagem),
            )

            conn.commit()
            return {"status": "Mensagem enviada e mensagens anteriores marcadas como respondidas"}
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao enviar mensagem")

@router.post("/receber-mensagem")
def receber_mensagem(email: str, anuncio_id: str, mensagem_data: MensagemRequest, tipo: str):
    """Registra uma mensagem recebida ou enviada"""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO conversas (email, anuncio_id) VALUES (?, ?)",
                (email, anuncio_id),
            )
            conversa = conn.execute(
                "SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?",
                (email, anuncio_id),
            ).fetchone()

            if not conversa:
                raise HTTPException(status_code=400, detail="Erro ao criar conversa")

            # Se a mensagem for recebida, marca todas as enviadas como respondidas
            if tipo == 'recebida':
                conn.execute(
                    """
                    UPDATE mensagens
                    SET respondida = TRUE
                    WHERE conversa_id = ?
                    AND tipo = 'enviada'
                    """,
                    (conversa["id"],),
                )
            # Se a mensagem for enviada, marca todas as recebidas como respondidas
            elif tipo == 'enviada':
                conn.execute(
                    """
                    UPDATE mensagens
                    SET respondida = TRUE
                    WHERE conversa_id = ?
                    AND tipo = 'recebida'
                    """,
                    (conversa["id"],),
                )

            conn.execute(
                """
                INSERT INTO mensagens (conversa_id, tipo, mensagem, respondida)
                VALUES (?, ?, ?, FALSE)
                """,
                (conversa["id"], tipo, mensagem_data.mensagem),
            )

            conn.commit()
            return {"status": f"Mensagem {tipo} registrada com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao receber mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao receber mensagem")

@router.get("/mensagem-existe")
def verificar_mensagem_existe(email: str, anuncio_id: str, mensagem: str, tipo: str):
    """Verifica se uma mensagem já existe na DB para um anúncio específico"""
    try:
        with get_db() as conn:
            # Busca a conversa
            conversa = conn.execute("SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?", 
                                  (email, anuncio_id)).fetchone()
            
            if not conversa:
                logger.info(f"Conversa não encontrada para anuncio_id: {anuncio_id}")
                return {"existe": False}
            
            # Verifica se a mensagem já existe
            mensagem_existe = conn.execute("""
                SELECT COUNT(*) FROM mensagens 
                WHERE conversa_id = ? 
                AND mensagem = ?
                AND tipo = ?
            """, (conversa["id"], mensagem, tipo)).fetchone()[0] > 0
            
            logger.info(f"Verificação de mensagem para anuncio_id {anuncio_id}: {'existe' if mensagem_existe else 'não existe'}")
            return {"existe": mensagem_existe}
    except Exception as e:
        logger.error(f"Erro ao verificar mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao verificar mensagem: {str(e)}")

@router.get("/mensagens")
def buscar_mensagens(email: str, tipo: str = None, conversa_id: int = None, anuncio_id: str = None, respondida: bool = None, searched_info: bool = None):
    """Retorna todas as mensagens de um usuário, com opção de filtrar por tipo, conversa, anúncio e status de resposta"""
    try:
        with get_db() as conn:
            # Query base otimizada com JOIN
            query = """
                SELECT 
                    c.id as conversa_id, 
                    c.email, 
                    c.anuncio_id,
                    c.nome_vendedor,
                    c.titulo_anuncio,
                    c.preco_anuncio,
                    c.searched_info,
                    c.created_at as conversa_created_at,
                    c.updated_at as conversa_updated_at,
                    m.id as mensagem_id, 
                    m.tipo, 
                    m.mensagem, 
                    m.respondida,
                    m.created_at as mensagem_created_at
                FROM conversas c
                JOIN mensagens m ON c.id = m.conversa_id
                WHERE c.email = ?
            """
            params = [email]

            # Adiciona filtros dinâmicos
            if tipo:
                query += " AND m.tipo = ?"
                params.append(tipo)
            if conversa_id:
                query += " AND c.id = ?"
                params.append(conversa_id)
            if anuncio_id:
                query += " AND c.anuncio_id = ?"
                params.append(anuncio_id)
            if respondida is not None:
                query += " AND m.respondida = ?"
                params.append(respondida)
            if searched_info is not None:
                if searched_info:
                    query += " AND c.searched_info IS NOT NULL"
                else:
                    query += " AND c.searched_info IS NULL"

            # Ordena por data de criação da mensagem
            query += " ORDER BY m.created_at ASC"

            mensagens = conn.execute(query, params).fetchall()

            # Organiza o resultado
            resultado = {}
            for msg in mensagens:
                conversa_id = msg["conversa_id"]
                if conversa_id not in resultado:
                    resultado[conversa_id] = {
                        "id": conversa_id,
                        "email": msg["email"],
                        "anuncio_id": msg["anuncio_id"],
                        "nome_vendedor": msg["nome_vendedor"],
                        "titulo_anuncio": msg["titulo_anuncio"],
                        "preco_anuncio": msg["preco_anuncio"],
                        "searched_info": msg["searched_info"],
                        "created_at": msg["conversa_created_at"],
                        "updated_at": msg["conversa_updated_at"],
                        "mensagens": []
                    }
                resultado[conversa_id]["mensagens"].append({
                    "id": msg["mensagem_id"],
                    "conversa_id": conversa_id,
                    "tipo": msg["tipo"],
                    "mensagem": msg["mensagem"],
                    "respondida": bool(msg["respondida"]),
                    "created_at": msg["mensagem_created_at"]
                })

            return {"conversas": list(resultado.values())}
    except Exception as e:
        logger.error(f"Erro ao buscar mensagens: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar mensagens")

@router.post("/atualizar-info-anuncio")
def atualizar_info_anuncio(email: str, anuncio_id: str, nome_vendedor: str, titulo_anuncio: str, preco_anuncio: str):
    """Atualiza as informações do anúncio na conversa"""
    try:
        # Verifica se a conversa existe
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Verifica se a conversa existe
            cursor.execute("""
                SELECT id FROM conversas 
                WHERE email = ? AND anuncio_id = ?
            """, (email, anuncio_id))
            
            conversa = cursor.fetchone()
            if not conversa:
                logger.error(f"Conversa não encontrada para email {email} e anúncio {anuncio_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Conversa não encontrada para email {email} e anúncio {anuncio_id}"
                )
            
            # Tenta atualizar as informações
            try:
                cursor.execute("""
                    UPDATE conversas 
                    SET nome_vendedor = ?,
                        titulo_anuncio = ?,
                        preco_anuncio = ?
                    WHERE email = ? AND anuncio_id = ?
                """, (nome_vendedor, titulo_anuncio, preco_anuncio, email, anuncio_id))
                
                if cursor.rowcount == 0:
                    logger.error(f"Nenhuma linha atualizada para email {email} e anúncio {anuncio_id}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Nenhuma linha atualizada para email {email} e anúncio {anuncio_id}"
                    )
                
                conn.commit()
                logger.info(f"Informações do anúncio atualizadas com sucesso para email {email} e anúncio {anuncio_id}")
                return {"status": "Informações do anúncio atualizadas com sucesso"}
                
            except sqlite3.Error as e:
                logger.error(f"Erro SQL ao atualizar informações do anúncio: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro SQL ao atualizar informações do anúncio: {str(e)}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao atualizar informações do anúncio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao atualizar informações do anúncio: {str(e)}"
        )

@router.get("/info-anuncio")
def buscar_info_anuncio(email: str, anuncio_id: str):
    """Retorna as informações do anúncio"""
    try:
        with get_db() as conn:
            info = conn.execute(
                """
                SELECT nome_vendedor, titulo_anuncio, preco_anuncio, searched_info
                FROM conversas
                WHERE email = ? AND anuncio_id = ?
                """,
                (email, anuncio_id)
            ).fetchone()
            
            if info:
                return {
                    "nome_vendedor": info["nome_vendedor"],
                    "titulo_anuncio": info["titulo_anuncio"],
                    "preco_anuncio": info["preco_anuncio"],
                    "searched_info": info["searched_info"]
                }
            else:
                return {}
    except Exception as e:
        logger.error(f"Erro ao buscar informações do anúncio: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar informações do anúncio")

@router.post("/atualizar-searched-info")
def atualizar_searched_info(email: str, anuncio_id: str, searched_info: str):
    """Atualiza o campo searched_info da conversa se ele ainda estiver vazio"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Verifica se a conversa existe e se searched_info está vazio
            cursor.execute("""
                SELECT id, searched_info FROM conversas 
                WHERE email = ? AND anuncio_id = ?
            """, (email, anuncio_id))
            
            conversa = cursor.fetchone()
            if not conversa:
                logger.error(f"Conversa não encontrada para email {email} e anúncio {anuncio_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Conversa não encontrada para email {email} e anúncio {anuncio_id}"
                )
            
            if conversa["searched_info"] is not None:
                logger.info(f"Campo searched_info já preenchido para email {email} e anúncio {anuncio_id}")
                return {"status": "Campo searched_info já está preenchido"}
            
            # Atualiza o campo searched_info
            cursor.execute("""
                UPDATE conversas 
                SET searched_info = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE email = ? AND anuncio_id = ?
            """, (searched_info, email, anuncio_id))
            
            if cursor.rowcount == 0:
                logger.error(f"Nenhuma linha atualizada para email {email} e anúncio {anuncio_id}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Nenhuma linha atualizada para email {email} e anúncio {anuncio_id}"
                )
            
            conn.commit()
            logger.info(f"Campo searched_info atualizado com sucesso para email {email} e anúncio {anuncio_id}")
            return {"status": "Campo searched_info atualizado com sucesso"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao atualizar searched_info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao atualizar searched_info: {str(e)}"
        ) 