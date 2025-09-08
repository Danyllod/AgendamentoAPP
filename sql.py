import sqlite3

conn = sqlite3.connect("instance/agendamento.db")  # Abre o banco
cursor = conn.cursor()

cursor.execute("SELECT * FROM user")  # Executa uma query
dados = cursor.fetchall()  # Busca os resultados

for linha in dados:
    print(linha)  # Exibe os dados no terminal

#conn.close()

# CPF do usuário a ser atualizado
cpf_usuario = "70032179103"

# Atualizar o campo is_admin para True (1)
cursor.execute("UPDATE user SET is_admin = 1 WHERE cpf = ?", (cpf_usuario,))

# Salvar e fechar conexão
conn.commit()
conn.close()

print("Usuário atualizado para admin com sucesso!")