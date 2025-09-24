from pydantic import BaseModel, validator
from datetime import date, time
from typing import List, Union, Dict
from decimal import Decimal

class ServicoRealizadoCreate(BaseModel):
    nome_cliente: str
    barbeiro: str
    servico: Union[str, List[str]]
    data_servico: date

    @validator('servico')
    def servico_nao_pode_ser_vazio(cls, v):
        if not v or (isinstance(v, list) and len(v) == 0):
            raise ValueError('É necessário selecionar pelo menos um serviço.')
        return v

class ServicoRealizado(ServicoRealizadoCreate):
    id_servico_realizado: int
    valor: float

class ServicoDetalheSchema(BaseModel):
    nome_cliente: str
    servico: str
    valor: Decimal

class RelatorioBarbeiroSchema(BaseModel):
    totalServicos: int
    totalValor: Decimal
    servicosPorCliente: List[ServicoDetalheSchema]

RelatorioGeralResponse = Dict[str, RelatorioBarbeiroSchema]

class RelatorioBarbeiroEspecificoSchema(BaseModel):
    barbeiro: str
    totalServicos: int
    totalValor: Decimal
    servicosPorCliente: List[ServicoDetalheSchema]

    class Config:
        from_attributes = True