import os

# Remove o banco de dados existente
db_path = os.path.join('instance', 'budget.db')
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Banco de dados removido com sucesso: {db_path}")
    except Exception as e:
        print(f"Erro ao remover banco de dados: {e}")
else:
    print("Banco de dados não encontrado. Será criado ao iniciar o aplicativo.")
