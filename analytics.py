def gerar_insights_para_persona(df):
    from collections import Counter

    top_clientes = df['cliente_nome'].value_counts().head(3)
    ticket_medio_produtos = round(df['pedido_venda_valor_subtotal'].mean(), 2)

    todos_produtos = []
    df['produtos'].str.split(' | ').apply(todos_produtos.extend)
    mais_vendidos = Counter(todos_produtos).most_common(3)

    df['hora'] = df['hora_pedido'].str.slice(0, 2).astype(int)
    top_horas = df['hora'].value_counts().sort_index()
    dias_semana = df['dia_semana_pedido'].value_counts()
    campanhas = df['pedido_venda_utm_campaign'].dropna().value_counts().head(3)
    genero = df['cliente_sexo'].value_counts()

    return {
        "top_clientes": top_clientes.to_dict(),
        "ticket_medio_produtos": ticket_medio_produtos,
        "produtos_mais_vendidos": mais_vendidos,
        "horas_com_mais_vendas": top_horas.to_dict(),
        "dias_com_mais_pedidos": dias_semana.to_dict(),
        "campanhas_mais_ativas": campanhas.to_dict(),
        "pedidos_por_genero": genero.to_dict()
    }
