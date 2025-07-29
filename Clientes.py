import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar
from controllers import db_utils # Para get_or_create_cliente, delete_record
from datetime import datetime # Para o TEMP_CPF

def app(): # <--- Todo o código da página deve estar aqui dentro
    st.title("👤 Clientes")

    # --- CONTROLE DE VISIBILIDADE DO BOTÃO DE EXCLUIR CLIENTES ---
    # Altere esta variável para True para exibir o botão de exclusão de Clientes
    _PERMITIR_EXCLUSAO_CLIENTES = False # <--- Mude para True para ativar o botão de excluir Clientes
    # --- FIM CONTROLE ---


    conn = conectar()
    cursor = conn.cursor()

    # Formulário de cadastro de cliente
    st.subheader("➕ Cadastrar Novo Cliente")
    with st.form("form_novo_cliente", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente", key="novo_cliente_nome") # Obrigatório
        cpf = st.text_input("CPF (Opcional)", key="novo_cliente_cpf") # Opcional
        telefone = st.text_input("Telefone (Opcional)", key="novo_cliente_telefone") # Opcional
        
        submitted = st.form_submit_button("Cadastrar Cliente")

        if submitted:
            if not nome:
                st.error("O nome do cliente é obrigatório.")
            else:
                # Controle de Duplicidade por Nome (se CPF não fornecido)
                cpf_to_insert_check = cpf.strip() if cpf else None
                if not cpf_to_insert_check:
                    cursor.execute("""
                        SELECT id, nome, cpf FROM Cliente 
                        WHERE nome = ? AND (cpf IS NULL OR cpf LIKE 'TEMP_CPF_%')
                    """, (nome.strip(),))
                    existing_clients_without_cpf = cursor.fetchall()

                    if existing_clients_without_cpf:
                        st.warning(f"Já existe(m) cliente(s) com o nome '{nome.strip()}' sem CPF definido. "
                                   f"Considere editar um existente ou preencha o CPF para um novo cadastro único.")
                        for c_id, c_name, c_cpf in existing_clients_without_cpf:
                            st.info(f"- ID: {c_id}, Nome: {c_name}, CPF (temporário): {c_cpf if c_cpf else 'N/A'}")
                        st.stop()

                try:
                    db_utils.get_or_create_cliente(cursor, nome, cpf, telefone)
                    conn.commit()
                    st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed: Cliente.cpf" in str(e):
                        st.error(f"Erro: Já existe um cliente com este CPF/Nome temporário. Detalhes: {e}")
                    else:
                        st.error(f"Erro de integridade ao cadastrar cliente: {e}")
                    conn.rollback()
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado ao cadastrar cliente: {e}")
                    conn.rollback()
                finally:
                    conn.close()


    # Visualizar e Editar Clientes
    st.subheader("📋 Clientes Cadastrados")

    conn = conectar()
    query_clientes = "SELECT id, nome, cpf, telefone FROM Cliente ORDER BY nome"
    df_clientes = pd.read_sql_query(query_clientes, conn)
    conn.close()

    if not df_clientes.empty:
        st.write("Edite as informações diretamente na tabela. Pressione Enter ou clique fora para aplicar as alterações.")

        # Configuração das colunas editáveis
        column_config_dict = {
            "id": st.column_config.Column("ID", width="small", disabled=True),
            "nome": st.column_config.TextColumn("Nome do Cliente", required=True),
            "cpf": st.column_config.TextColumn("CPF"),
            "telefone": st.column_config.TextColumn("Telefone")
        }

        edited_df = st.data_editor(
            df_clientes,
            column_config=column_config_dict,
            num_rows="fixed", # Cadastro via formulário
            hide_index=True,
            key="clientes_data_editor"
        )

        # Lógica para salvar alterações
        if st.button("Salvar Alterações dos Clientes"):
            changes_made = False
            conn = conectar()
            cursor = conn.cursor()

            for idx, edited_row in edited_df.iterrows():
                original_row = df_clientes[df_clientes['id'] == edited_row['id']].iloc[0]

                # Verificar se o nome, CPF ou telefone mudaram
                if (edited_row['nome'] != original_row['nome'] or
                    edited_row['cpf'] != original_row['cpf'] or
                    edited_row['telefone'] != original_row['telefone']):
                    
                    cliente_id = edited_row['id']
                    new_nome = edited_row['nome'].strip()
                    new_cpf = str(edited_row['cpf']).strip() if pd.notna(edited_row['cpf']) else None
                    new_telefone = str(edited_row['telefone']).strip() if pd.notna(edited_row['telefone']) else ''

                    if not new_nome:
                        st.error(f"Erro: Nome do cliente (ID: {cliente_id}) não pode ser vazio.")
                        conn.rollback()
                        continue

                    # Lógica para CPF opcional/único (na edição)
                    cpf_to_update = new_cpf
                    if not new_cpf:
                        if original_row['cpf'] and not str(original_row['cpf']).startswith("TEMP_CPF_"):
                            cpf_to_update = original_row['cpf']
                        else:
                            cpf_to_update = f"TEMP_CPF_{new_nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                            st.warning(f"CPF do cliente '{new_nome}' (ID: {cliente_id}) está vazio ou temporário. Usando novo CPF temporário: {cpf_to_update}")
                    
                    try:
                        cursor.execute("UPDATE Cliente SET nome = ?, cpf = ?, telefone = ? WHERE id = ?",
                                       (new_nome, cpf_to_update, new_telefone, cliente_id))
                        if cursor.rowcount > 0:
                            changes_made = True
                        else:
                            st.warning(f"Nenhuma alteração aplicada para cliente ID: {cliente_id}.")
                    except sqlite3.IntegrityError:
                        st.error(f"Erro: CPF '{cpf_to_update}' já existe para outro cliente. Não foi possível atualizar o cliente '{new_nome}'.")
                        conn.rollback()
                        continue
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado ao atualizar cliente: {e}")
                        conn.rollback()
                        continue

            conn.commit()

            if changes_made:
                st.success("Alterações nos clientes salvas com sucesso! Recarregando...")
                conn.close()
                st.rerun()
            else:
                st.info("Nenhuma alteração a ser salva nos clientes.")
                conn.close()
                
    else:
        st.info("Nenhum cliente cadastrado ainda. Use o formulário acima para adicionar um.")

    # --- Lógica para Deletar Clientes ---
    st.markdown("---")
    st.subheader("🗑️ Excluir Clientes")
    
    if st.session_state.usuario["permissao"] == "supervisor":
        # --- CONTROLE DE VISIBILIDADE DO BOTÃO DE EXCLUIR CLIENTES ---
        if _PERMITIR_EXCLUSAO_CLIENTES: # O botão só aparece se essa flag for True
            if not df_clientes.empty:
                clientes_para_excluir_nomes = st.multiselect(
                    "Selecione o(s) nome(s) do(s) cliente(s) para excluir:",
                    df_clientes['nome'].tolist(),
                    key="multiselect_delete_cliente"
                )

                if st.button("Excluir Cliente(s) Selecionado(s)", key="delete_cliente_button"):
                    if clientes_para_excluir_nomes:
                        conn = conectar()
                        deleted_count = 0
                        for cliente_name in clientes_para_excluir_nomes:
                            cursor = conn.cursor()
                            cursor.execute("SELECT id FROM Cliente WHERE nome = ?", (cliente_name,))
                            cliente_id_to_delete = cursor.fetchone()
                            
                            if cliente_id_to_delete:
                                # Verificar se o cliente tem OSs associadas (FOREIGN KEY constraint)
                                cursor.execute("SELECT COUNT(*) FROM OrdemDeServico WHERE cliente_id = ?", (cliente_id_to_delete[0],))
                                os_count = cursor.fetchone()[0]
                                if os_count > 0:
                                    st.error(f"Erro: Cliente '{cliente_name}' não pode ser excluído porque possui {os_count} Ordem(ns) de Serviço associada(s). Exclua as OSs primeiro.")
                                    conn.rollback()
                                    continue
                                
                                if db_utils.delete_record(conn, "Cliente", cliente_id_to_delete[0]):
                                    deleted_count += 1
                                else:
                                    st.error(f"Falha ao excluir cliente '{cliente_name}'.")
                            else:
                                st.warning(f"Cliente '{cliente_name}' não encontrado no banco de dados para exclusão.")
                        
                        conn.close()
                        if deleted_count > 0:
                            st.success(f"{deleted_count} Cliente(s) excluído(s) com sucesso!")
                            st.rerun()
                        else:
                            st.info("Nenhuma cliente foi excluída.")
                    else:
                        st.warning("Selecione pelo menos um Cliente para excluir.")
            else:
                st.info("Nenhum cliente para excluir.")
        else: # Mensagem se o botão de exclusão estiver desabilitado por flag
            st.info("A funcionalidade de exclusão de Clientes está desabilitada no momento.")
    else: # Mensagem se não for supervisor
        st.info("Apenas supervisores podem excluir clientes.")