import sqlite3
import os

# Conexão com o banco de dados (reutiliza a lógica de conectar)
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "database", "db.sqlite3")

def conectar():
    return sqlite3.connect(db_path)

def adicionar_usuario_e_consultores_teste():
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        # Adicionar Usuário Supervisor de Teste
        try:
            cursor.execute("INSERT INTO Consultor (nome, email, senha, permissao) VALUES (?, ?, ?, ?)",
                           ("Admin Teste", "teste@teste.com", "123", "supervisor"))
            print("✅ Usuário supervisor 'Admin Teste' adicionado com sucesso!")
        except sqlite3.IntegrityError:
            print("⚠️ Usuário supervisor 'Admin Teste' já existe. Ignorando.")

        # Adicionar Consultores específicos
        consultores_iniciais = [
            ("Nadylla", "nadylla@exemplo.com", "123", "consultor"), # Exemplo de consultor para VALTRA_NADYLLA
            ("Tainara", "tainara@exemplo.com", "123", "consultor"), # Exemplo de consultor para FENDT_TAINARA
            ("222TAI221", "tainara2@exemplo.com", "senha", "consultor"), # Consultor do exemplo FENDT
            ("216ANTO223", "antonio@exemplo.com", "senha", "consultor"), # Consultor do exemplo VALTRA
            ("223NADYLA", "nadylla2@exemplo.com", "senha", "consultor"), # Outro consultor de exemplo
            ("Supervisor Geral", "supervisor@exemplo.com", "admin", "supervisor") # Outro supervisor
        ]
        for nome, email, senha, permissao in consultores_iniciais:
            try:
                cursor.execute("INSERT INTO Consultor (nome, email, senha, permissao) VALUES (?, ?, ?, ?)",
                               (nome, email, senha, permissao))
                print(f"✅ Consultor '{nome}' adicionado com sucesso!")
            except sqlite3.IntegrityError:
                print(f"⚠️ Consultor '{nome}' já existe. Ignorando.")

        # --- NOVO: Adicionar Tipos de Máquina Padrão ---
        tipos_maquina_padrao = [
            "Trator", "Colheitadeira", "Pulverizador", "Plantadeira", "Implemento"
        ]
        for tipo_desc in tipos_maquina_padrao:
            try:
                cursor.execute("INSERT INTO TipoMaquina (descricao) VALUES (?)", (tipo_desc,))
                print(f"✅ Tipo de Máquina '{tipo_desc}' adicionado com sucesso!")
            except sqlite3.IntegrityError:
                print(f"⚠️ Tipo de Máquina '{tipo_desc}' já existe. Ignorando.")


        conn.commit()
    except Exception as e:
        print(f"❌ Ocorreu um erro ao adicionar dados de teste: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    adicionar_usuario_e_consultores_teste()