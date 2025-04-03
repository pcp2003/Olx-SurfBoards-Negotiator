from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MensagemRequest(BaseModel):
    mensagem: str

class Mensagem(BaseModel):
    id: int
    conversa_id: int
    tipo: str  # "enviada" ou "recebida"
    mensagem: str
    respondida: bool
    created_at: datetime

class Conversa(BaseModel):
    id: int
    email: str
    anuncio_id: str
    nome_vendedor: Optional[str] = None
    titulo_anuncio: Optional[str] = None
    preco_anuncio: Optional[str] = None
    searched_info: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    mensagens: List[Mensagem] 