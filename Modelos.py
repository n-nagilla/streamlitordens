import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar
from controllers import db_utils # Para db_utils.get_or_create_modelo

def app(): # <--- Todo o código da página deve estar aqui dentro
    st.title("⚙️ Modelos (Visibilidade Limitada)")
    st.info("Esta página não está no menu principal, use a página 'Máquinas' para gerenciar modelos.")

    conn = conectar()
    cursor = conn.cursor()

    # Carregar tipos de máquina para o selectbox
    cursor.execute("SELECT id, descricao FROM TipoMaquina ORDER BY descricao")
    tipos_maquina = cursor.fetchall()
    tipos_maquina_map = {descricao: id for id, descricao in tipos_maquina}
    tipos_maquina_nomes = [descricao for id, descricao in tipos_maquina]

    st.subheader("Cadastrar Novo Modelo")
    nome_modelo = st.text_input("Nome do Modelo")
    chassi = st.text_input("Chassi (opcional)")
    selected_tipo_maquina_nome = st.selectbox("Selecione o Tipo de Máquina", options=[""] + tipos_maquina_nomes)
    tipo_maquina_id = tipos_maquina_map.get(selected_tipo_maquina_nome) if selected_tipo_maquina_nome else None

    if st.button("Cadastrar Modelo"):
        if nome_modelo and tipo_maquina_id:
            try:
                db_utils.get_or_create_modelo(cursor, nome_modelo, chassi, tipo_maquina_id)
                conn.commit()
                st.success("Modelo cadastrado com sucesso!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Erro: Este modelo já existe ou há um problema.")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")
            finally:
                conn.close()
        else:
            st.warning("Nome do Modelo e Tipo de Máquina são obrigatórios.")

    st.subheader("Modelos Cadastrados")
    cursor.execute("""
        SELECT m.id, m.nome_modelo, m.chassi, tm.descricao
        FROM Modelo m
        JOIN TipoMaquina tm ON m.tipo_maquina_id = tm.id
        ORDER BY m.nome_modelo
    """)
    modelos = cursor.fetchall()
    if modelos:
        df_modelos = pd.DataFrame(modelos, columns=["ID", "Modelo", "Chassi", "Tipo de Máquina"])
        st.dataframe(df_modelos, hide_index=True)
    else:
        st.info("Nenhum modelo cadastrado.")
    conn.close()