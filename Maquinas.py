import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar
# Removidos: from controllers import db_utils (já que os formulários foram removidos)
import plotly.express as px # Para gráficos

def app(): # <--- Todo o código da página deve estar aqui dentro
    st.title("🔧 Máquinas")

    conn = conectar()
    cursor = conn.cursor()

    # --- REMOVIDO: Formulário de Cadastro de Tipo de Máquina ---
    # st.subheader("➕ Cadastrar Novo Tipo de Máquina")
    # ... (código do formulário removido) ...
    # st.markdown("---")

    # --- REMOVIDO: Formulário de Cadastro de Modelo de Máquina ---
    # st.subheader("➕ Cadastrar Novo Modelo de Máquina")
    # ... (código do formulário removido) ...
    # st.markdown("---")

    # --- Inventário de Máquinas e Filtros ---
    st.subheader("📋 Inventário de Máquinas")

    # Carregar todos os modelos e tipos de máquina
    query_inventario = """
    SELECT m.nome_modelo, m.chassi, tm.descricao AS tipo_maquina_descricao, c.nome AS cliente_responsavel
    FROM Modelo m
    JOIN TipoMaquina tm ON m.tipo_maquina_id = tm.id
    LEFT JOIN OrdemDeServico os ON m.id = os.modelo_id AND os.data_faturamento IS NULL
    LEFT JOIN Cliente c ON os.cliente_id = c.id
    ORDER BY tm.descricao, m.nome_modelo
    """
    df_inventario = pd.read_sql_query(query_inventario, conn)

    # Obter lista de tipos de máquina e modelos para filtro
    # As queries para popular os filtros permanecem, mesmo que os formulários de cadastro tenham saído
    cursor.execute("SELECT id, descricao FROM TipoMaquina ORDER BY descricao")
    tipos_maquina_db = cursor.fetchall()
    tipos_maquina_nomes = [desc for id, desc in tipos_maquina_db]

    cursor.execute("SELECT id, nome_modelo FROM Modelo ORDER BY nome_modelo")
    modelos_db = cursor.fetchall()
    modelos_nomes = [name for id, name in modelos_db]


    tipos_para_filtro = ["Todos"] + tipos_maquina_nomes
    modelos_para_filtro = ["Todos"] + modelos_nomes

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        tipo_selecionado = st.selectbox("Filtrar por Tipo de Máquina:", tipos_para_filtro)
    with col_filter2:
        modelo_selecionado = st.selectbox("Filtrar por Modelo:", modelos_para_filtro)

    df_filtrado = df_inventario.copy()
    if tipo_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_maquina_descricao'] == tipo_selecionado]
    if modelo_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nome_modelo'] == modelo_selecionado]

    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma máquina encontrada com os filtros aplicados.")

    st.markdown("---")

    # --- Dashboards de Pizza por Tipo de Máquina ---
    st.subheader("📊 Distribuição de Máquinas por Tipo")
    query_tipo_count = """
    SELECT tm.descricao AS tipo_maquina, COUNT(m.id) AS total_modelos
    FROM Modelo m
    JOIN TipoMaquina tm ON m.tipo_maquina_id = tm.id
    GROUP BY tm.descricao
    ORDER BY total_modelos DESC
    """
    df_tipo_count = pd.read_sql_query(query_tipo_count, conn)

    if not df_tipo_count.empty:
        fig_pie_tipo = px.pie(df_tipo_count, values='total_modelos', names='tipo_maquina',
                              title='Quantidade de Modelos por Tipo de Máquina',
                              hole=0.3)
        fig_pie_tipo.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie_tipo, use_container_width=True)
    else:
        st.info("Nenhum tipo de máquina para exibir no gráfico.")

    conn.close()