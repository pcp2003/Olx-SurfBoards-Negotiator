from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Mensagem(BaseModel):
    texto: str
    tipo: str  # 'recebida' ou 'enviada'
    data: Optional[datetime] = None

class Anuncio(BaseModel):
    id: str
    nome_vendedor: str
    titulo_anuncio: str
    preco_anuncio: str
    mensagens: List[Mensagem] = []
    ultima_atualizacao: Optional[datetime] = None 