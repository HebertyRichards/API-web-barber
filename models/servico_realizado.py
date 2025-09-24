from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

class ServicoRealizadoDB(BaseModel):
    id_servico_realizado: int
    nome_cliente: str
    barbeiro: str
    servico: str 
    valor: Decimal
    data_servico: date
    registrado_em: datetime