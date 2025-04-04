from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from contexto_ia import coletar_contexto_para_ia
from db import fetch_all, fetch_one
from queries import GET_PRODUTOS_LOJA, GET_CONTA_ID_POR_DOMINIO
import os
from dotenv import load_dotenv
import time
import logging
import json


load_dotenv()

# Configuração de logging para funcionar com uvicorn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

app = FastAPI()

# Middleware de CORS para permitir o acesso do front
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PersonaRequest(BaseModel):
    nome: str
    idade: str
    genero: str
    descricao: str
    autoriza_dados: bool
    dominio_loja: str

class InsightRequest(BaseModel):
    dominio_loja: str

@app.post("/generate_personas")
async def generate_personas(data: PersonaRequest):
    contexto_loja = ""

    if data.autoriza_dados:
        contexto_loja = coletar_contexto_para_ia(data.dominio_loja)

    prompt = f"""
Você é um assistente inteligente e simpático que ajuda lojistas a criar até 3 personas. 
Com base nas informações fornecidas, gere até 3 personas e retorne as seguintes informações:

- Nome e foto fictícia  
- Idade estimada
- Estilo de vida ou profissão
- Comportamento de compra
- Produtos mais comprados
- Canais de comunicação preferidos
- Sugestões práticas de comunicação, SEO e campanhas

Informações de um cliente real que o lojista conhece pessoalmente, descritas por ele:
- Nome: {data.nome}
- Idade: {data.idade}
- Gênero: {data.genero}
- Descrição: {data.descricao}

Retorne a resposta diretamente no formato JSON, não use blocos de código markdown, quebras de linha, escapes ou aspas adicionais.
As personas devem ser fictícias, mas devem ter características semelhantes ao cliente real descrito acima.
Deve retornar no json uma lista de personas e a estrutura deve exatamente esta:

{{
  "personas": [
    {{
      "nome": "...",
      "foto": "...",
      "idade": "...",
      "estilo_de_vida": "...",
      "comportamento_de_compra": "...",
      "produtos_mais_comprados": "...",
      "canais_de_comunicacao": "...",
      "sugestoes": "..."
    }},
    ...
  ]
}}   

{contexto_loja}
"""

    start_time = time.time()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um especialista em marketing e comportamento do consumidor, especializado na criação de personas detalhadas, realistas e úteis para estratégias comerciais. Com base nas informações fornecidas sobre uma loja e um cliente, você poderá criar personas fictícias completas e coerentes. Você é atento a todos os detalhes sejam consistentes e plausíveis."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
        temperature=0.8,
    )
    end_time = time.time()

    usage = response.usage
    logger.info("--- OPENAI API MÉTRICAS ---")
    logger.info(f"Tokens usados: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
    logger.info(f"Tempo de resposta: {round(end_time - start_time, 2)} segundos")
    logger.info("------------------------------")

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        logger.error("Resposta da IA não é um JSON válido.")
        return {"erro": "Resposta da IA inválida"}

@app.post("/insights")
def gerar_insights(data: InsightRequest):
    contexto = coletar_contexto_para_ia(data.dominio_loja)

    prompt = f"""
Com base nos dados de uma loja virtual brasileira apresentados abaixo, gere insights do tipo "Você sabia que...". As frases devem ser curtas, informativas e criadas a partir dos dados. Use percentual ao falar de proporção, valores em reais para preços, e dias da semana em português.
Use informações de gênero, idade, produtos mais vendidos, ticket médio, dias da semana com mais vendas, campanhas, horário de pico, e outros dados relevantes.
A resposta deve conter apenas insights como chave e explicações adicionais ou dicas de marketing como valor.
Não foque em clientes específicos e sim o que eles tem em comum.
Varie os insights, não repita informações e evite frases genéricas como "A loja vende produtos de moda".
Utilize dados públicos mais recentes de e-commerce brasileiro para enriquecer os insights, como tendências de mercado, comportamento de compra e preferências dos consumidores.
Quando for pertinente, você pode adicionar dicas de marketing, SEO e comunicação que sejam relevantes aos dados apresentados.
Retorne a resposta diretamente no formato JSON, sem usar blocos de código markdown ou aspas adicionais. A estrutura deve seguir exatamente:
{{
  "insights": [
    "...",
    "..."
  ]
}}

{contexto}
"""

    start_time = time.time()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um assistente de dados de e-commerce, especializado em insights para lojistas."},
            {"role": "user", "content": prompt},
        ],
                max_tokens=1000,
        temperature=0.7,
    )
    end_time = time.time()

    usage = response.usage
    logger.info("--- OPENAI API MÉTRICAS (INSIGHTS) ---")
    logger.info(f"Tokens usados: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
    logger.info(f"Tempo de resposta: {round(end_time - start_time, 2)} segundos")
    logger.info("------------------------------")

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        logger.error("Resposta da IA não é um JSON válido.")
        return {"erro": "Resposta da IA inválida"}
    
    
@app.post("/improve_products")
async def melhorar_produtos(data: InsightRequest):
    conta_id = fetch_one(GET_CONTA_ID_POR_DOMINIO.format(dominio=data.dominio_loja))
    if not conta_id:
        return {"erro": "Domínio não encontrado."}

    produtos = fetch_all(GET_PRODUTOS_LOJA.format(conta_id=conta_id))
    print(produtos)
    contexto = coletar_contexto_para_ia(data.dominio_loja)
    print(contexto)

    prompt = f"""
Com base nas personas e nos dados abaixo, analise os produtos e sugira melhorias que podem aumentar o interesse dos consumidores. Avalie nomes, preços, categorias, títulos e descrições SEO.

Retorne em formato JSON com a estrutura:
{{
  "melhorias": [
    {{
      "produto_nome": "...",
      "sugestao": "..."
    }}
  ]
}}

Personas e contexto:
{contexto}

Produtos da loja:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um assistente de e-commerce que sugere melhorias com base em perfis de clientes."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.7,
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        logger.error("Resposta da IA não é um JSON válido.")
        #return {"erro": "Resposta da IA inválida"}
        return response.choices[0].message.content

@app.post("/transcribe_audio")
async def transcribe_audio(file: UploadFile = File(...)):
    contents = await file.read()
    with open("temp_audio.wav", "wb") as audio_file:
        audio_file.write(contents)

    with open("temp_audio.wav", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )

    return {"transcription": transcript.text}
