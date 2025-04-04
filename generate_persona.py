from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from openai import OpenAI
import os
from dotenv import load_dotenv
from contexto_ia import novo_coletar_contexto_para_ia

import time


class PersonaRequest(BaseModel):
    """
    Modelo de request recebido via API, contendo dados de um cliente real
    e informações sobre a loja.
    """

    nome: str
    faixa_de_idade: Literal["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    genero: Literal["Masculino", "Feminino", "Não binário", "Não informado"]
    localidade: str = Field(
        ...,
        description=(
            "Cidade ou Região onde a persona mora. "
            "Ex: 'São Paulo - SP', 'Nordeste', 'Minas Gerais'."
        ),
    )
    faixa_de_renda: Literal[
        "Até R$ 2000,00",
        "De R$ 2000,00 a R$ 5000,00",
        "De R$ 5000,00 a R$ 10000,00",
        "Acima de R$ 10000,00",
    ]
    mais_informacoes: str = Field(
        ..., description="Outras informações que o lojista conhece sobre a persona."
    )
    autoriza_dados: bool
    dominio_loja: str


class PersonaResponse(BaseModel):
    nome_ficticio: str = Field(
        ...,
        description=(
            "Nome fictício da persona. "
            "Ex: 'Carlos Tecnológico', 'Marcia Fashion', 'João Econômico'. "
            "Deve representar uma característica marcante da persona."
        ),
    )
    foto: str = Field(
        ...,
        description=(
            "URL ilustrativa da persona. "
            "Ex: 'https://randomuser.me/api/portraits/men/32.jpg'."
        ),
    )
    idade: int = Field(
        ...,
        description=("Idade estimada da persona (apenas números). " "Ex: 25, 35, 42."),
    )
    genero: Literal["Masculino", "Feminino", "Não binário", "Não informado"] = Field(
        ...,
        description=(
            "Gênero da persona. As opções exatas são: "
            "'Masculino', 'Feminino', 'Não binário' ou 'Não informado'."
        ),
    )
    cidade: str = Field(
        ...,
        description=(
            "Cidade e estado onde a persona mora. "
            "Ex: 'São Paulo - SP', 'Recife - PE'."
        ),
    )
    faixa_renda: Literal[
        "Até R$ 2000,00",
        "De R$ 2000,00 a R$ 5000,00",
        "De R$ 5000,00 a R$ 10000,00",
        "Acima de R$ 10000,00",
    ] = Field(
        ...,
        description=(
            "Faixa de renda da persona. As opções exatas são: "
            "'Até R$ 2000,00', 'De R$ 2000,00 a R$ 5000,00', "
            "'De R$ 5000,00 a R$ 10000,00' ou 'Acima de R$ 10000,00'."
        ),
    )
    estilo_de_vida: str = Field(
        ...,
        description=(
            "Breve descrição do estilo de vida: hobbies, rotina, valores, interesses etc."
        ),
    )
    comportamento_de_compra: str = Field(
        ...,
        description=(
            "Resumo do comportamento de compra: o que busca ao consumir, "
            "frequência, motivações, canais preferidos e preocupações."
        ),
    )
    produtos_mais_comprados: str = Field(
        ...,
        description=(
            "Principais produtos comprados pela persona, "
            "podem ser exemplos pontuais baseados no contexto do lojista."
        ),
    )
    canais_de_comunicacao: str = Field(
        ...,
        description=(
            "Canais preferidos para se comunicar com marcas ou receber promoções. "
            "Ex: redes sociais, WhatsApp, e-mail etc."
        ),
    )
    sugestoes: str = Field(
        ...,
        description=(
            "Sugestões de marketing e comunicação para lidar com essa persona, "
            "incluindo ideias de campanhas e pontos de atenção."
        ),
    )


class ModelOutput(BaseModel):
    scratchpad: str = Field(
        ...,
        description=(
            "Espaço para anotações e raciocínio do modelo, onde ele deve explicar "
            "como chegou às personas e justificar suas escolhas."
        ),
    )
    personas: List[PersonaResponse] = Field(
        ..., description="Lista de até 3 personas. Gere no máximo 3 itens."
    )


class ModelInput(BaseModel):
    nome: str
    faixa_de_idade: Literal["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    genero: Literal["Masculino", "Feminino", "Não binário", "Não informado"]
    localidade: str
    faixa_de_renda: Literal[
        "Até R$ 2000,00",
        "De R$ 2000,00 a R$ 5000,00",
        "De R$ 5000,00 a R$ 10000,00",
        "Acima de R$ 10000,00",
    ]
    mais_informacoes: str
    contexto_loja: Optional[str] = None


def generate_personas(req: PersonaRequest):
    contexto_loja = novo_coletar_contexto_para_ia(req.dominio_loja)
    model_input = ModelInput(
        nome=req.nome,
        faixa_de_idade=req.faixa_de_idade,
        genero=req.genero,
        localidade=req.localidade,
        faixa_de_renda=req.faixa_de_renda,
        mais_informacoes=req.mais_informacoes,
        contexto_loja=contexto_loja,
    )

    return infer_personas(model_input)


SYSTEM_PROMPT = """
Você é um especialista em marketing e comportamento do consumidor. 
Sua tarefa é analisar dados de uma loja virtual (incluindo sua atividade, produtos mais vendidos, estatísticas, exemplos de pedidos) 
e também as informações fornecidas sobre um cliente real (nome, faixa de idade, renda etc.).

A partir desses dados, siga este passo a passo:
1. Leia atentamente as estatísticas e o contexto da loja.
2. Leia as informações do cliente real que o lojista conhece bem.
3. Planeje como esses dados podem inspirar até 3 personas (no máximo) que sejam úteis ao lojista, 
   mas lembre-se de criar **variedade** (por exemplo, diversidade de gênero e faixa etária, caso faça sentido).
4. Explique sua linha de raciocínio dentro de "scratchpad" – é seu espaço de anotações, onde você pode listar os principais pontos e o porquê de cada escolha.
5. Em seguida, produza até 3 objetos de persona na lista "personas".

O **formato** do JSON que você deve retornar é **exatamente**:

{
  "scratchpad": "",
  "personas": [
    {
      "nome_ficticio": "",
      "foto": "",
      "idade": 0,
      "genero": "",
      "cidade": "",
      "faixa_renda": "",
      "estilo_de_vida": "",
      "comportamento_de_compra": "",
      "produtos_mais_comprados": "",
      "canais_de_comunicacao": "",
      "sugestoes": ""
    }
  ]
}

**Instruções importantes**:
- Use somente as chaves "scratchpad" e "personas".
- Gere no máximo 3 itens em "personas".
- Não retorne texto fora do JSON.
- Idade deve ser um número inteiro, e a faixa_renda deve ser exatamente um dos valores permitidos.
- Garanta alguma variedade entre as personas (gênero, perfil socioeconômico, faixa etária etc.) para ilustrar diferentes potenciais públicos.

Seja coerente e consistente. Mencione no "scratchpad" qualquer insight que te leve a decidir cada persona.
"""


def infer_personas(model_input: ModelInput, system_prompt: str = SYSTEM_PROMPT):

    user_prompt = f"""
    Contexto da loja:
    {model_input.contexto_loja}

    Informações do cliente real (inspiração para as personas):
    - Nome: {model_input.nome}
    - Faixa de idade: {model_input.faixa_de_idade}
    - Gênero: {model_input.genero}
    - Localidade: {model_input.localidade}
    - Faixa de renda: {model_input.faixa_de_renda}
    - Observações adicionais: {model_input.mais_informacoes}

    Gere até 3 personas, no máximo, e escreva seu raciocínio passo a passo em 'scratchpad'.
    Lembre-se de retornar **exclusivamente** o JSON no formato descrito no system prompt,
    e procure diversificar gênero, idade ou outros aspectos que sejam relevantes para o mix de clientes.
    """

    start_time = time.time()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  # Ajuste para o modelo que você tiver disponível
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=4000,
        temperature=0.3,
        response_format=ModelOutput,
    )
    end_time = time.time()

    usage = response.usage
    print("--- OPENAI API MÉTRICAS (INSIGHTS) ---")
    print(
        f"Tokens usados: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}"
    )
    print(f"Tempo de resposta: {round(end_time - start_time, 2)} segundos")
    print("------------------------------")

    return response.choices[0].message


if __name__ == "__main__":
    load_dotenv()
    req = PersonaRequest(
        nome="Carlos",
        faixa_de_idade="25-34",
        genero="Masculino",
        localidade="Nordeste",
        faixa_de_renda="De R$ 2000,00 a R$ 5000,00",
        mais_informacoes=(
            "Carlos é um jovem de 25 anos que mora no Nordeste e trabalha como programador. "
            "Ele gosta de usar o celular para comprar produtos online e geralmente "
            "compra produtos de tecnologia e moda."
        ),
        autoriza_dados=True,
        dominio_loja="www.anmyperfumes.com.br",
    )
    response_data = generate_personas(req)
    print(response_data.parsed.model_dump_json(indent=4))
