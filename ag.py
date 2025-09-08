import sqlite3

# Caminho para o seu banco
db_path = "agendamento.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Apagar a tabela antiga (avaliacao), se existir
cursor.execute("DROP TABLE IF EXISTS avaliacao;")

# Criar a nova tabela avaliacoes
cursor.execute("""
CREATE TABLE IF NOT EXISTS avaliacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    doctor_id INTEGER NOT NULL,
    qualidade_medico TEXT,
    comentarios_medico TEXT,
    recepcao TEXT,
    recepcionista_nome TEXT,
    qualidade_recepcionista TEXT,
    comentarios_recepcionista TEXT,
    data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctor (id) ON DELETE CASCADE
);
""")

conn.commit()
conn.close()

print("Tabela 'avaliacoes' criada com sucesso!")
