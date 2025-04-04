# queries.py

GET_PEDIDOS_ULTIMOS_30_DIAS = """
SELECT
	A.pedido_venda_id,
	DATE_FORMAT(A.pedido_venda_data_criacao, '%Y-%m-%d') AS data_pedido,
	DATE_FORMAT(A.pedido_venda_data_criacao, '%H:%i:%s') AS hora_pedido,
	DATE_FORMAT(A.pedido_venda_data_criacao, '%W') AS dia_semana_pedido,
	A.cliente_id,
	SUBSTRING_INDEX(F.cliente_nome, ' ', 1) as cliente_nome, 
	F.cliente_data_nascimento,
	F.cliente_sexo,
	A.pedido_venda_valor_desconto,
	A.pedido_venda_valor_subtotal,
	A.pedido_venda_utm_campaign,
	GROUP_CONCAT(B.pedido_venda_item_nome SEPARATOR ' | ') AS produtos,
	C.pedido_venda_endereco_cidade,
	C.pedido_venda_endereco_estado,
	E.pagamento_nome
FROM
	lojaintegrada.pedido_tb_pedido_venda A
INNER JOIN lojaintegrada.pedido_tb_pedido_venda_item B 
	ON A.pedido_venda_id = B.pedido_venda_id
INNER JOIN lojaintegrada.pedido_tb_pedido_venda_endereco C 
	ON C.pedido_venda_endereco_id = A.pedido_venda_endereco_entrega_id 
INNER JOIN lojaintegrada.pedido_tb_pedido_venda_pagamento D 
	ON D.pedido_venda_id = A.pedido_venda_id 
INNER JOIN lojaintegrada.configuracao_tb_pagamento E 
	ON E.pagamento_id = D.pagamento_id 
INNER JOIN lojaintegrada.cliente_tb_cliente F 
	ON F.cliente_id = A.cliente_id
WHERE
	A.conta_id = {conta_id}
	AND A.pedido_venda_data_criacao >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY
	A.pedido_venda_id,
	A.pedido_venda_data_criacao,
	DATE_FORMAT(A.pedido_venda_data_criacao, '%H:%i:%s'),
	DATE_FORMAT(A.pedido_venda_data_criacao, '%W'),
	A.cliente_id,
	F.cliente_nome,
	F.cliente_data_nascimento,
	F.cliente_sexo,
	A.pedido_venda_valor_desconto,
	A.pedido_venda_valor_subtotal,
	A.pedido_venda_utm_campaign,
	C.pedido_venda_endereco_cidade,
	C.pedido_venda_endereco_estado,
	E.pagamento_nome
ORDER BY
	A.pedido_venda_id DESC
LIMIT 500;
"""
GET_CONTA_ID_POR_DOMINIO = """
SELECT conta_id 
FROM lojaintegrada.plataforma_tb_conta
WHERE conta_loja_dominio = '{dominio}'
LIMIT 1;
"""

GET_PRODUTOS_LOJA = """
select
	distinct A.produto_nome,
	B.produto_preco_cheio,
	B.produto_preco_promocional,
	E.categoria_nome,
	C.seo_title,
	C.seo_description	
from
	lojaintegrada.catalogo_tb_produto A
inner join lojaintegrada.catalogo_tb_produto_preco B on
	B.produto_id = A.produto_id
inner join lojaintegrada.marketing_tb_seo C on
	C.seo_linha_id = A.produto_id
inner join lojaintegrada.catalogo_tb_produto_categoria D
	on D.produto_id = A.produto_id
inner join lojaintegrada.catalogo_tb_categoria E
	on E.categoria_id = D.categoria_id
where
	A.produto_tipo = 'normal' and
	A.produto_ativo = true and
	A.conta_id = {conta_id}
limit 10;
"""