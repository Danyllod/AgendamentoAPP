from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from faq import responder_faq
import os
import re
import sqlite3
import redis
import hashlib
from dotenv import load_dotenv

# Carregar variáveis do .env, sobrescrevendo as existentes
load_dotenv(override=True)

# Configuração do Redis via variáveis de ambiente
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379").split()[0])
REDIS_TTL = int(os.getenv("REDIS_TTL", "3600").split()[0])  # padrão = 1h

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

# Busca histórico no banco de mensagens
def buscar_historico(numero, limite=3):
    try:
        conn = sqlite3.connect("mensagens.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT texto, resposta FROM mensagens
            WHERE numero = ?
            ORDER BY id DESC
            LIMIT ?
        """, (numero, limite))
        historico = cursor.fetchall()
        return list(reversed(historico))
    except Exception as e:
        print(f"❌ Erro ao buscar histórico: {e}")
        return []
    finally:
        conn.close()

# Chave da API do Gemini
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "SUA_CHAVE_AQUI")

# Inicializa Gemini
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
prompt = ChatPromptTemplate.from_template("{mensagem}")
parser = StrOutputParser()
chain = prompt | llm | parser

# Filtro de mensagens ofensivas ou inválidas
def mensagem_invalida(mensagem):
    texto = mensagem.strip().lower()
    if len(texto) < 3:
        return "Desculpe, a mensagem está muito curta. Por favor, envie uma pergunta mais completa."
    palavroes = ["idiota", "burro", "merda", "droga", "porra", "puta", "caralho", "bosta", "cu", "buceta", "rola", "pica"]
    if any(p in texto for p in palavroes):
        return "Linguagem ofensiva não é permitida. Por favor, seja respeitoso."
    if re.fullmatch(r"[!?.\\s]*", texto):
        return "Por favor, envie uma mensagem com conteúdo mais claro."
    if len(set(texto)) <= 3:
        return "A mensagem parece repetitiva demais. Poderia reformular?"
    return None

# Gera uma chave hash segura para cache no Redis
def gerar_chave(prompt_input):
    return "cache:" + hashlib.sha256(prompt_input.encode()).hexdigest()

# Função principal
def responder_mensagem(mensagem, numero=None):
    erro = mensagem_invalida(mensagem)
    if erro:
        return erro

    # 🔹 1. Verificar no FAQ com cache
    faq_cache_key = gerar_chave("faq:" + mensagem.lower().strip())
    resposta_cache_faq = redis_client.get(faq_cache_key)
    if resposta_cache_faq:
        print("🔄 Resposta FAQ obtida do cache Redis")
        return resposta_cache_faq

    resposta_faq = responder_faq(mensagem)
    if resposta_faq:
        redis_client.setex(faq_cache_key, REDIS_TTL, resposta_faq)
        print("✅ Resposta encontrada no FAQ e salva no cache Redis.")
        return resposta_faq

    # 🔹 2. Montar contexto com histórico
    historico = buscar_historico(numero) if numero else []
    contexto = ""
    for pergunta, resposta in historico:
        contexto += f"Usuário: {pergunta}\nAssistente: {resposta}\n"

    prompt_input = contexto + f"Usuário: {mensagem}\nAssistente:"
    chave_cache = gerar_chave(prompt_input)

    # 🔹 3. Verificar cache no Redis
    cache_resposta = redis_client.get(chave_cache)
    if cache_resposta:
        print("🔁 Resposta LLM obtida do cache Redis")
        return cache_resposta

    # 🔹 4. Consultar Gemini e salvar no Redis
    try:
        print(f"⚡ Cache MISS — consultando Gemini...")
        resposta = chain.invoke({"mensagem": prompt_input}).strip()
        redis_client.setex(chave_cache, REDIS_TTL, resposta)
        print("✅ Resposta salva no cache Redis.")
        return resposta
    except Exception as e:
        print(f"❌ Erro ao chamar Gemini: {e}")
        return "Desculpe, houve um erro ao gerar a resposta. Se precisar, procure o Hospital CRESM."
