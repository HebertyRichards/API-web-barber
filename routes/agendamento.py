import aiomysql
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Union

from config.database import get_db_pool
from config.email import send_email
from schemas.agendamento import AgendamentoCreate
from datetime import date
from schemas.agendamento import HorariosIndisponiveisResponse 

agendamento_router = APIRouter(
    prefix="/agendamentos",
    tags=["Agendamentos"]
)

def format_email_body(
    nome_cliente: str, 
    data_agendamento: str, 
    horario: str, 
    barbeiro: str, 
    servico: Union[str, List[str]], 
    codigo: int
) -> str:
    
    lista_servicos = ""
    if isinstance(servico, list):
        lista_servicos = "".join([f"<li>{s}</li>" for s in servico])
    else:
        lista_servicos = f"<li>{servico}</li>"

    mensagem = f"""
        <h1>Agendamento Concluído</h1>
        <p>Olá {nome_cliente}, seu agendamento foi concluído no dia {data_agendamento} às {horario} com o barbeiro {barbeiro}.</p>
        <p>Segue o(s) serviço(s) agendado(s):</p>
        <ul>
            {lista_servicos}
        </ul>
        <p>O código do seu agendamento é: <strong>{codigo}</strong></p>
        <p>Para cancelar, acesse <a href="https://web-barber-phi.vercel.app/cancelar-agendamento">Cancelar Agendamento</a> e insira o código.</p>
        <p>A barbearia Web Barber-Shop agradece a preferência. Venha ficar novo de novo!</p>
    """
    return mensagem

@agendamento_router.post("/agendar", status_code=status.HTTP_201_CREATED)
async def criar_agendamento(
    agendamento: AgendamentoCreate, 
    db_pool: aiomysql.Pool = Depends(get_db_pool)
):
    servicos_str = ", ".join(agendamento.servico) if isinstance(agendamento.servico, list) else agendamento.servico
    
    sql = """
        INSERT INTO agendamentos 
        (nome_cliente, telefone, email, data_agendamento, horario, servico, barbeiro) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (
                    agendamento.nome_cliente,
                    agendamento.telefone,
                    agendamento.email,
                    agendamento.data_agendamento,
                    agendamento.horario,
                    servicos_str,
                    agendamento.barbeiro
                ))
                new_id = cursor.lastrowid

    except aiomysql.Error as err:
        print(f"Erro ao inserir no banco: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erro ao salvar agendamento"
        )

    if agendamento.email:
        try:
            body = format_email_body(
                nome_cliente=agendamento.nome_cliente,
                data_agendamento=agendamento.data_agendamento.strftime('%d-%m-%Y'),
                horario=agendamento.horario.strftime('%H:%M'),
                barbeiro=agendamento.barbeiro,
                servico=agendamento.servico,
                codigo=new_id
            )
            await send_email(
                subject="Agendamento Confirmado!",
                recipients=[agendamento.email],
                body=body
            )
            return {
                "message": "Agendamento criado e e-mail enviado com sucesso!",
                "agendamento_id": new_id
            }
        except Exception as e:
            print(f"Erro ao enviar o e-mail: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agendamento salvo com ID {new_id}, mas ocorreu um erro ao enviar o e-mail de confirmação."
            )
    else:
        return {
            "message": "Agendamento criado com sucesso! Nenhum e-mail enviado porque o campo 'email' não foi preenchido.",
            "agendamento_id": new_id
        }

def format_cancel_email_body(
    nome_cliente: str, data_agendamento: str, horario: str, barbeiro: str, servicos: str
) -> str:
    lista_servicos_html = "".join([f"<li>{s.strip()}</li>" for s in servicos.split(',')])
    mensagem = f"""
        <h1>Agendamento Cancelado</h1>
        <p>Olá {nome_cliente}, seu agendamento para o dia {data_agendamento} às {horario} com o barbeiro {barbeiro} foi cancelado com sucesso.</p>
        <p>Serviço(s) que estava(m) agendado(s):</p>
        <ul>{lista_servicos_html}</ul>
        <p>Se você não solicitou este cancelamento ou tiver alguma dúvida, por favor, entre em contato conosco.</p>
        <p>Atenciosamente, Barbearia Web Barber-Shop.</p>
    """
    return mensagem

@agendamento_router.delete("/cancelar-agendamento/{id_agendamento}", status_code=status.HTTP_200_OK)
async def cancelar_agendamento(
    id_agendamento: int,
    db_pool: aiomysql.Pool = Depends(get_db_pool)
):
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            sql_select = "SELECT * FROM agendamentos WHERE id_agendamento = %s"
            await cursor.execute(sql_select, (id_agendamento,))
            agendamento = await cursor.fetchone()

            if not agendamento:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado.")
            
            sql_delete = "DELETE FROM agendamentos WHERE id_agendamento = %s"
            await cursor.execute(sql_delete, (id_agendamento,))

            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado para deleção.")

    if agendamento.get("email"):
        try:
            data_formatada = agendamento["data_agendamento"].strftime('%d/%m/%Y')
            hora_formatada = agendamento["horario"].strftime('%H:%M')
            body = format_cancel_email_body(
                nome_cliente=agendamento["nome_cliente"],
                data_agendamento=data_formatada,
                horario=hora_formatada,
                barbeiro=agendamento["barbeiro"],
                servicos=agendamento["servico"]
            )
            await send_email(
                subject="Seu Agendamento foi Cancelado",
                recipients=[agendamento["email"]],
                body=body
            )
            return {"message": "Agendamento cancelado com sucesso e e-mail de notificação enviado!"}
        except Exception as e:
            print(f"Erro ao enviar e-mail de cancelamento: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agendamento cancelado, mas erro ao enviar e-mail de notificação."
            )
    
    return {"message": "Agendamento cancelado com sucesso!"}

@agendamento_router.get(
    "/horarios", 
    response_model=HorariosIndisponiveisResponse
)
async def listar_horarios_indisponiveis(
    data: date, 
    barbeiro: str,
    db_pool: aiomysql.Pool = Depends(get_db_pool)
):
    sql = "SELECT horario FROM agendamentos WHERE data_agendamento = %s AND barbeiro = %s"

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (data, barbeiro))
                results = await cursor.fetchall()
    except aiomysql.Error as err:
        print(f"Erro ao buscar horários: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao consultar os horários no banco de dados."
        )

    horarios_ocupados = [row[0] for row in results]
    
    return {"horariosIndisponiveis": horarios_ocupados}