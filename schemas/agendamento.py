from pydantic import BaseModel, validator, Field
from datetime import date, time
from typing import Optional, List, Union

class AgendamentoBase(BaseModel):
    nome_cliente: str = Field(..., max_length=255)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    data_agendamento: date
    horario: time
    servico: Union[str, List[str]]
    barbeiro: str = Field(..., max_length=255)

    @validator('email', always=True)
    def check_email_or_telefone(cls, v, values):
        if not v and not values.get('telefone'):
            raise ValueError('Por favor, preencha o telefone ou o email.')
        return v

class AgendamentoCreate(AgendamentoBase):
    pass

class Agendamento(AgendamentoBase):
    id_agendamento: int 

    class Config:
        from_attributes = True