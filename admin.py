import sqlite3

conn = sqlite3.connect("instance/agendamento.db")  # Abre o banco
cursor = conn.cursor()

cursor.execute("SELECT * FROM user")  # Executa uma query
dados = cursor.fetchall()  # Busca os resultados

for linha in dados:
    print(linha)  # Exibe os dados no terminal


# CPF do usuário a ser atualizado
cpf_usuario = "03122348489"

# Atualizar o campo is_admin para True (1)
cursor.execute("UPDATE user SET CPF = ADMIN WHERE cpf = ?", (cpf_usuario,))

# Salvar e fechar conexão
conn.commit()
conn.close()

print("Usuário atualizado para admin com sucesso!")