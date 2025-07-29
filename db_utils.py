import sqlite3
from datetime import datetime
from controllers.auth import conectar # Importa a função de conexão

def get_or_create_cliente(cursor, nome, cpf, telefone):
    if not nome or str(nome).strip() == '':
        raise ValueError("Nome do cliente não pode ser vazio.")

    cpf_to_use = str(cpf).strip() if cpf else None
    
    # --- NOVO: Lógica para evitar duplicidade de clientes SEM CPF ---
    if not cpf_to_use: # Se o CPF não foi fornecido (é None ou string vazia)
        # Tenta encontrar um cliente existente com o mesmo nome E sem CPF (ou com TEMP_CPF)
        cursor.execute("""
            SELECT id FROM Cliente 
            WHERE nome = ? AND (cpf IS NULL OR cpf LIKE 'TEMP_CPF_%')
        """, (nome.strip(),))
        existing_client_id_by_name_no_cpf = cursor.fetchone()

        if existing_client_id_by_name_no_cpf:
            # Se encontrou um cliente com o mesmo nome E sem CPF/TEMP_CPF, reutiliza
            cliente_id = existing_client_id_by_name_no_cpf[0]
            # Opcional: Atualizar telefone ou nome (se algo mudou) no cliente existente
            cursor.execute("UPDATE Cliente SET nome = ?, telefone = ? WHERE id = ?", (nome, telefone, cliente_id))
            return cliente_id
        else:
            # Se não encontrou cliente com mesmo nome e sem CPF, gera um novo TEMP_CPF único
            cpf_to_use = f"TEMP_CPF_{nome.replace(' ', '_').upper()}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    # --- FIM NOVO ---
    
    # Se o CPF foi fornecido (cpf_to_use não é None e não é TEMP_CPF_ gerado agora), 
    # ou se foi gerado um novo TEMP_CPF_
    cursor.execute("SELECT id FROM Cliente WHERE cpf = ?", (cpf_to_use,))
    cliente_id = cursor.fetchone()
    if cliente_id:
        # Se encontrou, atualiza nome e telefone (para o caso de ser um CPF existente)
        cursor.execute("UPDATE Cliente SET nome = ?, telefone = ? WHERE id = ?", (nome, telefone, cliente_id[0]))
        return cliente_id[0]
    else:
        # Se não encontrou (novo cliente com CPF, ou novo TEMP_CPF_ gerado), insere
        cursor.execute("INSERT INTO Cliente (nome, cpf, telefone) VALUES (?, ?, ?)", (nome, cpf_to_use, telefone))
        return cursor.lastrowid

def get_or_create_tipo_maquina(cursor, descricao):
    if not descricao or str(descricao).strip() == '':
        descricao = "Tipo Desconhecido" # Default
    cursor.execute("SELECT id FROM TipoMaquina WHERE descricao = ?", (descricao,))
    tipo_id = cursor.fetchone()
    if tipo_id:
        return tipo_id[0]
    else:
        cursor.execute("INSERT INTO TipoMaquina (descricao) VALUES (?)", (descricao,))
        return cursor.lastrowid

def get_or_create_status(cursor, descricao):
    if not descricao or str(descricao).strip() == '':
        descricao = "Status Desconhecido" # Default
    cursor.execute("SELECT id FROM Status WHERE descricao = ?", (descricao,))
    status_id = cursor.fetchone()
    if status_id:
        return status_id[0]
    else:
        cursor.execute("INSERT INTO Status (descricao) VALUES (?)", (descricao,))
        return cursor.lastrowid

def get_or_create_modelo(cursor, nome_modelo, chassi, tipo_maquina_id):
    if not nome_modelo or str(nome_modelo).strip() == '':
        raise ValueError("Nome do modelo não pode ser vazio.")
    
    cursor.execute("SELECT id FROM Modelo WHERE nome_modelo = ? AND tipo_maquina_id = ?", (nome_modelo, tipo_maquina_id))
    modelo_id = cursor.fetchone()
    if modelo_id:
        cursor.execute("UPDATE Modelo SET chassi = ? WHERE id = ?", (chassi, modelo_id[0]))
        return modelo_id[0]
    else:
        cursor.execute("INSERT INTO Modelo (nome_modelo, chassi, tipo_maquina_id) VALUES (?, ?, ?)", (nome_modelo, chassi, tipo_maquina_id))
        return cursor.lastrowid

def get_consultor_id_by_name(cursor, nome_consultor):
    if not nome_consultor or str(nome_consultor).strip() == '':
        return None
    cursor.execute("SELECT id FROM Consultor WHERE nome = ?", (nome_consultor,))
    consultor_id = cursor.fetchone()
    if consultor_id:
        return consultor_id[0]
    return None

def get_consultor_name_by_id(cursor, consultor_id):
    if not consultor_id:
        return "N/A"
    cursor.execute("SELECT nome FROM Consultor WHERE id = ?", (consultor_id,))
    consultor_name = cursor.fetchone()
    if consultor_name:
        return consultor_name[0]
    return "Desconhecido"

def delete_record(conn, table_name, record_id):
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA foreign_keys = ON;")
        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Erro de integridade ao deletar registro da tabela {table_name} (ID: {record_id}): {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Erro inesperado ao deletar registro da tabela {table_name} (ID: {record_id}): {e}")
        conn.rollback()
        return False