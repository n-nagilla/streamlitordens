import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar
import plotly.express as px # Para gráficos (barras ou linhas)

def app(): # <--- Todo o código da página deve estar aqui dentro
    st.title("✅ Ordens de Serviço Faturadas")

    conn = conectar()
    cursor = conn.cursor()

    # --- Obter Anos e Meses Disponíveis para Filtro ---
    query_anos = """
    SELECT DISTINCT strftime('%Y', data_faturamento) AS ano
    FROM OrdemDeServico
    WHERE data_faturamento IS NOT NULL
    ORDER BY ano DESC
    """
    df_anos = pd.read_sql_query(query_anos, conn)
    anos_disponiveis = ["Todos"] + df_anos['ano'].tolist()

    col_filter_ano, col_filter_mes = st.columns(2)
    with col_filter_ano:
        ano_selecionado = st.selectbox("Filtrar por Ano:", anos_disponiveis)

    meses_disponiveis = ["Todos", "01-Janeiro", "02-Fevereiro", "03-Março", "04-Abril",
                         "05-Maio", "06-Junho", "07-Julho", "08-Agosto",
                         "09-Setembro", "10-Outubro", "11-Novembro", "12-Dezembro"]
    with col_filter_mes:
        mes_selecionado = st.selectbox("Filtrar por Mês:", meses_disponiveis)

    # Converter mês selecionado para formato numérico para query
    mes_num_selecionado = None
    if mes_selecionado != "Todos":
        mes_num_selecionado = meses_disponiveis.index(mes_selecionado)
        if mes_num_selecionado < 10: # Adiciona zero à esquerda para meses < 10
            mes_str = f"0{mes_num_selecionado}"
        else:
            mes_str = str(mes_num_selecionado)
    else:
        mes_str = None # Reset se 'Todos'

    # --- CONSTRUÇÃO DAS QUERIES COM FILTROS ---

    # Base da query com filtro de faturamento
    base_query = """
    FROM OrdemDeServico os
    JOIN Cliente c ON os.cliente_id = c.id
    JOIN Modelo m ON os.modelo_id = m.id
    JOIN Consultor con ON os.consultor_id = con.id
    JOIN Status s ON os.status_id = s.id
    WHERE os.data_faturamento IS NOT NULL
    """
    base_params = []

    # Adicionar filtro de consultor (se aplicável)
    if st.session_state.usuario["permissao"] == "consultor":
        base_query += f" AND os.consultor_id = {st.session_state.usuario['id']}"
    
    # Adicionar filtro de ano
    if ano_selecionado != "Todos":
        base_query += f" AND strftime('%Y', os.data_faturamento) = ?"
        base_params.append(ano_selecionado)

    # Adicionar filtro de mês
    if mes_str: # mes_str já está no formato 'MM'
        base_query += f" AND strftime('%m', os.data_faturamento) = ?"
        base_params.append(mes_str)


    # 1. Query para KPIs (Quantidade e Valor Total Faturado)
    query_kpis = f"""
    SELECT
        COUNT(os.id) AS total_faturadas, -- CORRIGIDO: COUNT(os.id)
        SUM(REPLACE(REPLACE(os.valor_liquido, 'R$', ''), ',', '.')) AS valor_total_faturado
    {base_query}
    """
    df_kpis = pd.read_sql_query(query_kpis, conn, params=base_params)

    # 2. Query para o Gráfico Mensal
    query_faturadas_mensal = f"""
    SELECT
        strftime('%Y-%m', data_faturamento) AS mes_ano,
        COUNT(os.id) AS total_faturadas -- CORRIGIDO: COUNT(os.id)
    {base_query}
    GROUP BY mes_ano ORDER BY mes_ano
    """
    df_faturadas_mensal = pd.read_sql_query(query_faturadas_mensal, conn, params=base_params)

    # 3. Query para o Gráfico Anual (ignora filtro de mês)
    # Cria uma cópia dos parâmetros base para a query anual, pois ela não terá filtro de mês
    base_params_anual = list(base_params) 
    base_query_anual = base_query
    if mes_str: # Se o mês foi filtrado, remove o filtro de mês da query anual
        base_query_anual = base_query_anual.replace(f" AND strftime('%m', os.data_faturamento) = ?", "")
        # Remove o último parâmetro adicionado se for o do mês
        if len(base_params_anual) > 0 and mes_str in base_params_anual[-1:]:
            base_params_anual.pop()


    query_faturadas_anual = f"""
    SELECT
        strftime('%Y', data_faturamento) AS ano,
        COUNT(os.id) AS total_faturadas
    {base_query_anual}
    GROUP BY ano ORDER BY ano
    """
    df_faturadas_anual = pd.read_sql_query(query_faturadas_anual, conn, params=base_params_anual)

    # 4. Query para os Detalhes da Tabela
    query_os_faturadas_detalhes = f"""
    SELECT
        os.id, os.numero_os, os.tipo_os,
        c.nome AS cliente_nome,
        c.cpf AS cliente_cpf,
        c.telefone AS cliente_telefone,
        s.descricao AS status_descricao,
        m.nome_modelo AS modelo_nome,
        con.nome AS consultor_nome,
        m.chassi AS modelo_chassi,
        os.data_abertura,
        os.valor_liquido,
        os.data_faturamento,
        os.data_pagamento_fabrica,
        os.descricao_servico
    {base_query}
    ORDER BY os.data_faturamento DESC
    """
    df_os_faturadas_detalhes = pd.read_sql_query(query_os_faturadas_detalhes, conn, params=base_params)

    conn.close()

    # --- Exibição dos KPIs ---
    st.subheader("Indicadores de Ordens Faturadas")
    
    total_faturadas_kpi = df_kpis['total_faturadas'].iloc[0] if not df_kpis.empty else 0
    # Converte para float antes da formatação para garantir que é um número
    valor_total_faturado_kpi = float(df_kpis['valor_total_faturado'].iloc[0]) if not df_kpis.empty and pd.notna(df_kpis['valor_total_faturado'].iloc[0]) else 0.0

    col_kpi1, col_kpi2 = st.columns(2)
    with col_kpi1:
        st.metric(label="Quantidade Total Faturada", value=int(total_faturadas_kpi))
    with col_kpi2:
        st.metric(label="Valor Total Faturado", value=f"R$ {valor_total_faturado_kpi:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("---")

    # --- Gráficos de Barras para Quantidade de Faturadas ---
    st.subheader("Total de Ordens Faturadas por Período")

    if not df_faturadas_mensal.empty:
        fig_mensal = px.bar(df_faturadas_mensal, x='mes_ano', y='total_faturadas',
                            title='OSs Faturadas por Mês/Ano',
                            labels={'mes_ano': 'Mês/Ano', 'total_faturadas': 'Quantidade de OSs'})
        st.plotly_chart(fig_mensal, use_container_width=True)
    else:
        st.info("Nenhum dado de OS faturada por mês/ano para exibir.")

    if not df_faturadas_anual.empty:
        fig_anual = px.bar(df_faturadas_anual, x='ano', y='total_faturadas',
                           title='OSs Faturadas por Ano',
                           labels={'ano': 'Ano', 'total_faturadas': 'Quantidade de OSs'})
        st.plotly_chart(fig_anual, use_container_width=True)
    else:
        st.info("Nenhum dado de OS faturada por ano para exibir.")

    st.markdown("---")

    # --- Detalhes das OS Faturadas ---
    st.subheader("Detalhes das Ordens de Serviço Faturadas")
    if not df_os_faturadas_detalhes.empty:
        # Converter valor_liquido para formato de moeda para exibição na tabela
        df_os_faturadas_detalhes['valor_liquido'] = df_os_faturadas_detalhes['valor_liquido'].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else ""
        )
        st.dataframe(df_os_faturadas_detalhes, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma Ordem de Serviço detalhada encontrada com os filtros aplicados.")