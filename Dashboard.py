import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar
from controllers import db_utils # Para get_consultor_id_by_name e get_consultor_name_by_id
import plotly.express as px # Necessário para os gráficos

def app(): # <--- Todo o código da página deve estar aqui dentro
    st.title("📊 Dashboard Geral")

    conn = conectar()
    cursor = conn.cursor() # Abrir cursor para queries auxiliares

    # --- Funções auxiliares para dados de Consultores (Cacheando para performance) ---
    @st.cache_data
    def get_consultores_data_for_dashboard():
        conn_inner = conectar()
        cursor_inner = conn_inner.cursor()
        cursor_inner.execute("SELECT id, nome FROM Consultor ORDER BY nome")
        consultores_db = cursor_inner.fetchall()
        conn_inner.close()
        consultores_map = {nome: id for id, nome in consultores_db}
        consultores_nomes = [nome for id, nome in consultores_db]
        return consultores_map, consultores_nomes

    consultores_map, consultores_nomes = get_consultores_data_for_dashboard()

    # --- Filtro de Consultor para Supervisor ---
    consultor_id_para_exibicao = None # Por padrão, não há filtro por consultor específico
    consultor_nome_para_exibicao = "Todos os Consultores" # Nome para exibição no título

    if st.session_state.usuario["permissao"] == "supervisor":
        st.sidebar.subheader("Filtrar Dashboard")
        opcoes_filtro_consultor = ["Todos os Consultores"] + consultores_nomes
        selected_consultor_sidebar = st.sidebar.selectbox("Visualizar dados de:", opcoes_filtro_consultor, key="dashboard_consultor_filter")

        if selected_consultor_sidebar == "Todos os Consultores":
            consultor_id_para_exibicao = None
            consultor_nome_para_exibicao = "Todos os Consultores"
        else:
            consultor_id_para_exibicao = consultores_map.get(selected_consultor_sidebar)
            consultor_nome_para_exibicao = selected_consultor_sidebar
            if consultor_id_para_exibicao is None:
                st.error("Erro: Consultor selecionado para filtro não encontrado.")
                consultor_id_para_exibicao = None

    elif st.session_state.usuario["permissao"] == "consultor":
        # Se for um consultor, ele só vê os próprios dados
        consultor_id_para_exibicao = st.session_state.usuario["id"]
        consultor_nome_para_exibicao = st.session_state.usuario["nome"]
        st.sidebar.info(f"Visualizando dados de: {consultor_nome_para_exibicao}")


    # --- CONSTRUÇÃO DAS QUERIES COM FILTROS ---

    # Base da query com filtro de OS em aberto
    base_query_aberto = """
    FROM OrdemDeServico os
    JOIN Cliente c ON os.cliente_id = c.id
    JOIN Consultor cm ON os.consultor_id = cm.id
    JOIN Status s ON os.status_id = s.id
    JOIN Modelo m ON os.modelo_id = m.id
    WHERE os.data_faturamento IS NULL -- Filtra apenas OS em aberto
    """
    base_params_aberto = []

    # Aplicar o filtro de consultor (se houver) a todas as queries
    if consultor_id_para_exibicao:
        base_query_aberto += f" AND os.consultor_id = ?"
        base_params_aberto.append(consultor_id_para_exibicao)

    # NOVO: Checkbox para filtrar por OSs com mais de 30 dias
    st.markdown("---")
    show_over_30_days = st.checkbox("Mostrar apenas OSs com mais de 30 dias em aberto")
    if show_over_30_days:
        base_query_aberto += f" AND JULIANDAY('now') - JULIANDAY(os.data_abertura) > 30"


    # Query para o DataFrame principal (tabela de detalhes de OS em aberto)
    query_os_detalhes = f"""
    SELECT os.id, os.numero_os, os.tipo_os,
        c.nome AS cliente,
        cm.nome AS consultor,
        s.descricao AS status_descricao,
        m.nome_modelo AS modelo_nome,
        m.chassi AS modelo_chassi,
        os.descricao_servico,
        os.data_abertura,
        os.valor_liquido
    {base_query_aberto}
    ORDER BY os.data_abertura DESC
    """
    df_os_detalhes = pd.read_sql_query(query_os_detalhes, conn, params=base_params_aberto)

    # --- CORREÇÃO: Converter data_abertura para objeto datetime.date ---
    df_os_detalhes['data_abertura'] = pd.to_datetime(df_os_detalhes['data_abertura'], errors='coerce').dt.date

    # Query para contagem de ordens POR STATUS (APENAS EM ABERTO)
    query_status_count = f"""
    SELECT s.descricao AS status, COUNT(os.id) AS total_ordens
    {base_query_aberto}
    GROUP BY s.descricao ORDER BY total_ordens DESC
    """
    params_status_count = []
    
    # Query para OSs em Aberto vs. Mais de 30 Dias (APENAS EM ABERTO)
    query_os_em_aberto_dias = f"""
    SELECT
        CASE
            WHEN JULIANDAY('now') - JULIANDAY(os.data_abertura) > 30 THEN 'Ordens de serviço +30⚠️'
            ELSE 'O.S. em Aberto (até 30 dias)'
        END AS grupo_status_dias,
        COUNT(os.id) AS total_ordens
    {base_query_aberto}
    GROUP BY grupo_status_dias ORDER BY grupo_status_dias DESC
    """
    params_os_em_aberto_dias = []
    
    df_status_count = pd.read_sql_query(query_status_count, conn, params=base_params_aberto)
    df_os_em_aberto_dias = pd.read_sql_query(query_os_em_aberto_dias, conn, params=base_params_aberto)

    conn.close()


    st.subheader(f"Visão Geral das Ordens de Serviço em Aberto ({consultor_nome_para_exibicao})")


    # --- Botão para Limpar Cache (APENAS SUPERVISOR) ---
    if st.session_state.usuario["permissao"] == "supervisor":
        if st.button("🔄 Limpar Cache de Dados do Dashboard"):
            st.cache_data.clear()
            st.success("Cache limpo! Recarregando dados...")
            st.rerun()
    st.markdown("---")


    # --- DESTAQUE PRINCIPAL: KPIs de Total e Alerta (LADO A LADO) ---
    col_kpi_principal1, col_kpi_principal2 = st.columns(2)
    
    total_geral_os_aberto = df_status_count['total_ordens'].sum() if not df_status_count.empty else 0
    with col_kpi_principal1:
        st.metric(label="Total Geral de Ordens em Aberto", value=int(total_geral_os_aberto))
    
    os_mais_30_dias = df_os_em_aberto_dias[df_os_em_aberto_dias['grupo_status_dias'] == 'Ordens de serviço +30⚠️']['total_ordens'].sum() if 'Ordens de serviço +30⚠️' in df_os_em_aberto_dias['grupo_status_dias'].tolist() else 0
    with col_kpi_principal2:
        if os_mais_30_dias > 0:
            st.markdown(
                f"""
                <style>
                div[data-testid="stMetricValue"][data-st-css-ffrje4] {{ color: red; }}
                </style>
                """,
                unsafe_allow_html=True
            )
        st.metric(label="Ordens de serviço +30⚠️", value=int(os_mais_30_dias))
    
    st.markdown("---")


    # --- Detalhes de Todas as Ordens de Serviço em Aberto (MOVIDO PARA CIMA) ---
    
    # Campo de seleção para filtrar a tabela por status
    all_status_options = ["Todos os Status"] + df_status_count['status'].tolist()
    selected_status_filter = st.selectbox("Filtrar tabela por Status:", options=all_status_options, key="dashboard_status_table_filter")

    # Filtrar a tabela de detalhes baseada na seleção do status
    df_os_detalhes_filtered_by_status = df_os_detalhes.copy()
    if selected_status_filter != "Todos os Status":
        df_os_detalhes_filtered_by_status = df_os_detalhes_filtered_by_status[
            df_os_detalhes_filtered_by_status['status_descricao'] == selected_status_filter
        ]

    if not df_os_detalhes_filtered_by_status.empty:
        df_os_detalhes_filtered_by_status['valor_liquido'] = df_os_detalhes_filtered_by_status['valor_liquido'].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else ""
        )
        df_os_detalhes_filtered_by_status['data_abertura'] = df_os_detalhes_filtered_by_status['data_abertura'].apply(
            lambda x: x.strftime('%d/%m/%Y') if x is not None else ""
        )
        st.dataframe(df_os_detalhes_filtered_by_status, use_container_width=True)
    else:
        st.info("Nenhuma Ordem de Serviço em aberto encontrada para o seu perfil com os filtros aplicados.")

    st.markdown("---")

    # --- Gráficos de Pizza em Colunas ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("### OS Em Aberto: Tempo na Garantia")
        if not df_os_em_aberto_dias.empty:
            df_em_aberto_filtered = df_os_em_aberto_dias[
                df_os_em_aberto_dias['grupo_status_dias'].isin(['Ordens de serviço +30⚠️', 'O.S. em Aberto (até 30 dias)'])
            ]
            if not df_em_aberto_filtered.empty:
                fig_pie_dias = px.pie(df_em_aberto_filtered, values='total_ordens', names='grupo_status_dias',
                                     title='OS Em Aberto: Tempo na Garantia',
                                     hole=0.3)
                fig_pie_dias.update_traces(textposition='inside', textinfo='value+label')
                if 'Ordens de serviço +30⚠️' in df_em_aberto_filtered['grupo_status_dias'].tolist():
                    fig_pie_dias.update_traces(marker_colors=['red' if s == 'Ordens de serviço +30⚠️' else 'lightgray' for s in df_em_aberto_filtered['grupo_status_dias']])
                st.plotly_chart(fig_pie_dias, use_container_width=True)
            else:
                st.info("Nenhuma OS em aberto (<=30 ou >30 dias) para exibir neste gráfico.")
        else:
            st.info("Nenhum dado de OS em aberto por tempo para exibir.")

    with chart_col2:
        st.write("### Distribuição de Ordens por Status")
        if not df_status_count.empty:
            fig_pie_status = px.pie(df_status_count, values='total_ordens', names='status',
                             title='Distribuição de Ordens de Serviço por Status',
                             hole=0.3)
            fig_pie_status.update_traces(textposition='inside', textinfo='value+label')
            st.plotly_chart(fig_pie_status, use_container_width=True)
        else:
            st.info("Nenhum dado de status de Ordem de Serviço em aberto para exibir no gráfico.")