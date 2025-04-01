from pydantic import BaseModel
from typing import List

class MensagemRequest(BaseModel):
    mensagem: str

class Mensagem(BaseModel):
    id: int
    conversa_id: int
    tipo: str  # "enviada" ou "recebida"
    mensagem: str
    respondida: bool

class Conversa(BaseModel):
    id: int
    email: str
    anuncio_id: str
    mensagens: List[Mensagem] 