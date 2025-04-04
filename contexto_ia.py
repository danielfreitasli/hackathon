# contexto_ia.py

from db import fetch_one, fetch_all
from queries import GET_PEDIDOS_ULTIMOS_30_DIAS, GET_CONTA_ID_POR_DOMINIO
from analytics import gerar_insights_para_persona
import pandas as pd

def formatar_amostra_para_prompt(amostra):
    linhas = []
    for pedido in amostra:
        campos = [f"{chave}: {valor}" for chave, valor in pedido.items()]
        linha = "- " + ", ".join(campos)
        linhas.append(linha)
    return "\n".join(linhas)

def coletar_contexto_para_ia(dominio_loja: str) -> str:
    query_conta = GET_CONTA_ID_POR_DOMINIO.format(dominio=dominio_loja)
    conta_id = fetch_one(query_conta)
    if not conta_id:
        return "Não foi possível encontrar a loja com esse domínio."

    query = GET_PEDIDOS_ULTIMOS_30_DIAS.format(conta_id=conta_id)
    resultados = fetch_all(query)
    if not resultados:
        return "A loja não possui pedidos nos últimos 30 dias."

    df = pd.DataFrame(resultados)
    insights = gerar_insights_para_persona(df)
    amostra = df.sample(n=min(5, len(df)), random_state=42).to_dict(orient="records")

    # Enviar os dados brutos e sumarizados para a IA inferir o resto
    return (
        f"Estatísticas da loja:\n"
        f"- Ticket médio: R$ {insights['ticket_medio_produtos']}\n"
        f"- Produtos mais vendidos: {[p[0] for p in insights['produtos_mais_vendidos']]}\n"
        f"- Top 3 clientes: {list(insights['top_clientes'].items())}\n"
        f"- Distribuição por gênero: {insights['pedidos_por_genero']}\n"
        f"- Campanhas mais ativas: {list(insights['campanhas_mais_ativas'].keys())}\n"
        f"- Dias com mais pedidos: {list(insights['dias_com_mais_pedidos'].keys())}\n"
        f"- Horas com mais pedidos: {list(insights['horas_com_mais_vendas'].keys())}\n"
        f"\nExemplos reais de pedidos:\n{formatar_amostra_para_prompt(amostra)}"
    )
