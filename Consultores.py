import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar
from controllers import db_utils # Para get_consultor_id_by_name, get_consultor_name_by_id, delete_record


def app(): # <--- A função app não aceita mais 'mode'
    st.title("🧑‍💼 Gerenciamento de Consultores")

    conn = conectar()
    cursor = conn.cursor()

    # --- Funcionalidade de Cadastro de Consultor (APENAS PARA SUPERVISOR) ---
    if st.session_state.usuario["permissao"] == "supervisor":
        st.subheader("➕ Cadastrar Novo Consultor")
        with st.form("form_novo_consultor", clear_on_submit=True):
            nome_novo = st.text_input("Nome Completo do Consultor", key="novo_consultor_nome_form")
            email_novo = st.text_input("E-mail do Consultor", key="novo_consultor_email_form")
            senha_nova = st.text_input("Senha do Consultor", type="password", key="novo_consultor_senha_form")
            permissao_nova = st.selectbox("Permissão do Consultor", ["consultor", "supervisor"], key="novo_consultor_permissao_form")

            submitted = st.form_submit_button("Cadastrar Consultor")

            if submitted:
                if nome_novo and email_novo and senha_nova:
                    try:
                        cursor.execute("INSERT INTO Consultor (nome, email, senha, permissao) VALUES (?, ?, ?, ?)",
                                       (nome_novo, email_novo, senha_nova, permissao_nova))
                        conn.commit()
                        st.success(f"Consultor '{nome_novo}' cadastrado com sucesso!")
                        st.rerun() # Recarrega para atualizar a lista
                    except sqlite3.IntegrityError:
                        st.error("Erro: Já existe um consultor com este e-mail.")
                        conn.rollback()
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado ao cadastrar consultor: {e}")
                        conn.rollback()
                else:
                    st.warning("Preencha todos os campos obrigatórios para o consultor.")
    else:
        st.info("Apenas supervisores podem cadastrar novos consultores.")

    st.markdown("---")


    # --- Lista Completa de Consultores Cadastrados (VISUALIZAÇÃO SIMPLES) ---
    st.subheader("📋 Lista Completa de Consultores Cadastrados")

    cursor.execute("SELECT id, nome, email, permissao FROM Consultor ORDER BY nome")
    consultores_db_raw = cursor.fetchall()
    
    if consultores_db_raw:
        df_consultores = pd.DataFrame(consultores_db_raw, columns=["ID", "Nome", "E-mail", "Permissão"])
        st.dataframe(df_consultores, hide_index=True)
    else:
        st.info("Nenhum consultor cadastrado no sistema.")

    st.markdown("---")


    # --- Lógica para Excluir Consultores (APENAS PARA SUPERVISOR) ---
    st.subheader("🗑️ Excluir Consultores")
    
    if st.session_state.usuario["permissao"] == "supervisor":
        if consultores_db_raw: # Usa os dados brutos carregados para a lista
            consultores_nomes_disponiveis = [nome for id, nome, _, _ in consultores_db_raw]
            consultores_map_para_excluir = {nome: id for id, nome, _, _ in consultores_db_raw}

            consultores_para_excluir_nomes = st.multiselect(
                "Selecione o(s) nome(s) do(s) consultor(es) para excluir:",
                consultores_nomes_disponiveis,
                key="multiselect_delete_consultor"
            )

            if st.button("Excluir Consultor(es) Selecionado(s)", key="delete_consultor_button"):
                if consultores_para_excluir_nomes:
                    deleted_count = 0
                    for c_name in consultores_para_excluir_nomes:
                        c_id_to_delete = consultores_map_para_excluir.get(c_name)
                        if c_id_to_delete:
                            if c_id_to_delete == st.session_state.usuario['id']:
                                st.error(f"Erro: Você não pode excluir sua própria conta de usuário.")
                                conn.rollback()
                                continue
                            
                            # Verificar se o consultor tem OSs associadas (FOREIGN KEY constraint)
                            cursor.execute("SELECT COUNT(*) FROM OrdemDeServico WHERE consultor_id = ?", (c_id_to_delete,))
                            os_count = cursor.fetchone()[0]
                            if os_count > 0:
                                st.error(f"Erro: Consultor '{c_name}' não pode ser excluído porque possui {os_count} Ordem(ns) de Serviço associada(s).")
                                conn.rollback()
                                continue

                            if db_utils.delete_record(conn, "Consultor", c_id_to_delete):
                                deleted_count += 1
                                st.info(f"Consultor '{c_name}' excluído.")
                            else:
                                st.error(f"Falha ao excluir consultor '{c_name}'.")
                        else:
                            st.warning(f"Consultor '{c_name}' não encontrado no banco de dados para exclusão.")
                    
                    conn.commit()
                    if deleted_count > 0:
                        st.success(f"{deleted_count} Consultor(es) excluído(s) com sucesso! Recarregando...")
                        st.rerun()
                    else:
                        st.info("Nenhum consultor foi excluído.")
                else:
                    st.warning("Selecione pelo menos um Consultor para excluir.")
        else:
            st.info("Nenhum consultor para excluir.")
    else: # Se não for supervisor
        st.info("Apenas supervisores podem excluir consultores.")


    conn.close() # Fecha a conexão no final da função app()