import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar
from controllers import db_utils # Para db_utils.get_or_create_status

def app(): # <--- Todo o código da página deve estar aqui dentro
    st.title("🚦 Status de Ordem de Serviço (Visibilidade Limitada)")
    st.info("Esta página não está no menu principal, o status é gerenciado na página de Ordens de Serviço.")

    conn = conectar()
    cursor = conn.cursor()

    st.subheader("Cadastrar Novo Status")
    descricao = st.text_input("Descrição do Status")
    if st.button("Cadastrar Status"):
        if descricao:
            try:
                db_utils.get_or_create_status(cursor, descricao)
                conn.commit()
                st.success("Status cadastrado com sucesso!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Erro: Este status já existe.")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")
            finally:
                conn.close()
        else:
            st.warning("A descrição é obrigatória.")

    st.subheader("Status Cadastrados")
    cursor.execute("SELECT id, descricao FROM Status ORDER BY descricao")
    status_list = cursor.fetchall()
    if status_list:
        df_status = pd.DataFrame(status_list, columns=["ID", "Descrição"])
        st.dataframe(df_status, hide_index=True)
    else:
        st.info("Nenhum status cadastrado.")
    conn.close()