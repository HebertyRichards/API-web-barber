import re
import aiomysql
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict

from config.database import get_db_pool
from schemas.servico_realizado import ServicoRealizadoCreate
from schemas.servico_realizado import RelatorioGeralResponse, RelatorioBarbeiroEspecificoSchema

servico_router = APIRouter(
    prefix="/servicos-realizados",
    tags=["Serviços Realizados"]
)

def extrair_e_somar_valores(servicos: List[str]) -> Decimal:
    regex = r"R\$ ?(\d+,\d{2})"
    valores_decimais = []

    for s in servicos:
        match = re.search(regex, s)
        if match:
            valor_str = match.group(1).replace(',', '.')
            try:
                valores_decimais.append(Decimal(valor_str))
            except InvalidOperation:
                continue
    
    
    if not valores_decimais:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum valor de serviço válido encontrado no formato 'R$ XX,XX'."
        )

    return sum(valores_decimais)

@servico_router.post("/", status_code=status.HTTP_201_CREATED)
async def registrar_servico_realizado(
    servico_data: ServicoRealizadoCreate,
    db_pool: aiomysql.Pool = Depends(get_db_pool)
):
    servicos_list = servico_data.servico if isinstance(servico_data.servico, list) else [servico_data.servico]

    valor_total = extrair_e_somar_valores(servicos_list)
    servico_texto = " + ".join(servicos_list)

    sql = """
        INSERT INTO servicos_realizados (nome_cliente, barbeiro, servico, valor, data_servico)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (
                    servico_data.nome_cliente,
                    servico_data.barbeiro,
                    servico_texto,
                    valor_total,
                    servico_data.data_servico
                ))
                new_id = cursor.lastrowid
    except aiomysql.Error as err:
        print(f"Erro ao registrar serviço: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao registrar o serviço."
        )

    return {
        "message": "Serviço registrado com sucesso.",
        "id_servico_realizado": new_id,
        "valor_total_calculado": float(valor_total)
    }

@servico_router.get(
    "/relatorio/geral",
    response_model=RelatorioGeralResponse,
    tags=["Relatórios"]
)
async def gerar_relatorio_geral(
    db_pool: aiomysql.Pool = Depends(get_db_pool)
):
    sql = "SELECT barbeiro, nome_cliente, servico, valor FROM servicos_realizados"
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql)
                todos_os_servicos = await cursor.fetchall()
    except aiomysql.Error as err:
        print(f"Erro ao buscar relatório geral: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar dados para o relatório."
        )
    relatorio: Dict[str, dict] = {}

    for servico_db in todos_os_servicos:
        barbeiro = servico_db["barbeiro"]
        valor_servico = servico_db["valor"]
        if barbeiro not in relatorio:
            relatorio[barbeiro] = {
                "totalServicos": 0,
                "totalValor": Decimal("0.0"),
                "servicosPorCliente": []
            }

        relatorio[barbeiro]["totalServicos"] += 1
        relatorio[barbeiro]["totalValor"] += valor_servico
        
        relatorio[barbeiro]["servicosPorCliente"].append({
            "nome_cliente": servico_db["nome_cliente"],
            "servico": servico_db["servico"],
            "valor": valor_servico
        })

    return relatorio

@servico_router.get(
    "/relatorio/barbeiro/{nome_barbeiro}",
    response_model=RelatorioBarbeiroEspecificoSchema,
    tags=["Relatórios"]
)
async def gerar_relatorio_por_barbeiro(
    nome_barbeiro: str,
    db_pool: aiomysql.Pool = Depends(get_db_pool)
):
    sql = "SELECT nome_cliente, servico, valor FROM servicos_realizados WHERE barbeiro = %s"
    
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (nome_barbeiro,))
                servicos_do_barbeiro = await cursor.fetchall()
    except aiomysql.Error as err:
        print(f"Erro ao buscar relatório do barbeiro: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar dados para o relatório."
        )

    if not servicos_do_barbeiro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum serviço encontrado para o barbeiro '{nome_barbeiro}'."
        )

    total_servicos = len(servicos_do_barbeiro)
    total_valor = sum(servico['valor'] for servico in servicos_do_barbeiro)

    return {
        "barbeiro": nome_barbeiro,
        "totalServicos": total_servicos,
        "totalValor": total_valor,
        "servicosPorCliente": servicos_do_barbeiro
    }