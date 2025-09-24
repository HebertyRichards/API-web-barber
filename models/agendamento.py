from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class Agendamento(BaseModel):
    id: int
    nome_cliente: str
    telefone: Optional[str]
    email: Optional[str]
    data_agendamento: date
    horario: time
    servico: str
    barbeiro: str