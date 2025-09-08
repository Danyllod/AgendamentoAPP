import os
import json
import redis

# Configuração do Redis via variáveis de ambiente
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

CACHE_TTL = int(os.getenv("REDIS_TTL", "3600").split()[0])

FAQ_FILE = "data/faq.json"

# Carrega FAQ do arquivo JSON
with open(FAQ_FILE, "r", encoding="utf-8") as f:
    FAQ = json.load(f)

def responder_faq(mensagem):
    texto = mensagem.lower().strip()

    # Tenta buscar no cache
    cache_key = f"faq:{texto}"
    resposta_cache = redis_client.get(cache_key)
    if resposta_cache:
        print("🔄 Resposta obtida do cache Redis")
        return resposta_cache

    # Busca no FAQ
    for pergunta, resposta in FAQ.items():
        if pergunta in texto:
            redis_client.setex(cache_key, CACHE_TTL, resposta)
            return resposta

    return None
