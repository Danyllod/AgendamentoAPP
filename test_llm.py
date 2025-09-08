import os
import redis
from faq import responder_faq
from llm_agent import responder_mensagem

# Configura Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def test_faq_cache():
    pergunta = "telefone do cresm"

    # Limpa cache antes do teste
    redis_client.flushdb()

    # Primeira chamada (deve vir do FAQ, não do cache)
    resp1 = responder_faq(pergunta)
    assert resp1 is not None, "FAQ não respondeu!"
    assert "CRESM" in resp1 or "(62)" in resp1, "Resposta inesperada do FAQ"

    # Segunda chamada (deve vir do cache)
    resp2 = responder_faq(pergunta)
    assert resp2 == resp1, "Respostas diferentes!"
    print("✅ FAQ com cache funcionando!")

def test_llm_cache():
    pergunta = "qual a função do CRESM?"
    numero = "5511999999999"

    # Limpa cache antes do teste
    redis_client.flushdb()

    # Primeira chamada (vai gerar resposta nova)
    resp1 = responder_mensagem(pergunta, numero)
    assert resp1 is not None, "LLM não respondeu!"
    print("✅ Primeira resposta LLM gerada.")

    # Segunda chamada (deve vir do cache)
    resp2 = responder_mensagem(pergunta, numero)
    assert resp2 == resp1, "Cache não funcionou para LLM"
    print("✅ Cache da LLM funcionando!")

if __name__ == "__main__":
    print("🚀 Iniciando testes...")
    test_faq_cache()
    test_llm_cache()
    print("🎯 Todos os testes passaram!")
