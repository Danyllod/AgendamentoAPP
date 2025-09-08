import sqlite3

def init_db():
    conn = sqlite3.connect("mensagens.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            texto TEXT,
            resposta TEXT
        )
    """)
    conn.commit()
    conn.close()

def salvar_mensagem(numero, texto, resposta):
    try:
        conn = sqlite3.connect("mensagens.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mensagens (numero, texto, resposta) VALUES (?, ?, ?)", (numero, texto, resposta))
        conn.commit()
    except Exception as e:
        print(f"❌ Erro ao salvar mensagem no banco: {e}")
    finally:
        conn.close()

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
        return list(reversed(historico))  # Ordem cronológica
    except Exception as e:
        print(f"❌ Erro ao buscar histórico: {e}")
        return []
    finally:
        conn.close()
