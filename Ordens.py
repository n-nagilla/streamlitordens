import streamlit as st
import sqlite3
import pandas as pd
from controllers.auth import conectar # Para a conexão com o DB
from controllers import db_utils # Para as funções utilitárias (get_or_create, delete_record)
from datetime import datetime, date 

# --- Funções auxiliares para Selectboxes (Cacheando para performance) ---
@st.cache_data # st.cache_data é mais robusto para dados
def get_all_auxiliary_data():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome FROM Cliente")
    clientes_db = cursor.fetchall()
    clientes_map = {nome: id for id, nome in clientes_db}
    clientes_nomes = [nome for id, nome in clientes_db]

    cursor.execute("SELECT id, descricao FROM TipoMaquina")
    tipos_maquina_db = cursor.fetchall()
    tipos_maquina_map = {desc: id for id, desc in tipos_maquina_db}
    tipos_maquina_descricoes = [desc for id, desc in tipos_maquina_db]

    cursor.execute("SELECT id, nome_modelo, tipo_maquina_id FROM Modelo")
    modelos_db = cursor.fetchall()
    modelos_map_id_to_name = {id: name for id, name, _ in modelos_db}
    modelos_map_name_to_id = {name: id for id, name, _ in modelos_db}
    modelos_nomes = [name for id, name, _ in modelos_db]

    cursor.execute("SELECT id, nome FROM Consultor")
    consultores_db = cursor.fetchall()
    consultores_map = {nome: id for id, nome in consultores_db}
    consultores_nomes = [nome for id, nome in consultores_db] # Lista de nomes de consultores

    cursor.execute("SELECT id, descricao FROM Status")
    status_db = cursor.fetchall()
    status_map = {desc: id for id, desc in status_db}
    status_descricoes = [desc for id, desc in status_db] # Variável correta
    
    conn.close()
    return clientes_map, clientes_nomes, tipos_maquina_map, tipos_maquina_descricoes, \
           modelos_map_id_to_name, modelos_map_name_to_id, modelos_nomes, \
           consultores_map, consultores_nomes, status_map, status_descricoes


def app():
    st.title("📝 Ordens de Serviço")

    (clientes_map, clientes_nomes, tipos_maquina_map, tipos_maquina_descricoes,
     modelos_map_id_to_name, modelos_map_name_to_id, modelos_nomes,
     consultores_map, consultores_nomes, status_map, status_descricoes) = get_all_auxiliary_data()

    # --- Formulário para Nova Ordem de Serviço ---
    st.subheader("➕ Cadastrar Nova Ordem de Serviço")
    with st.form("form_nova_os", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            numero_os = st.text_input("Número da OS", help="Obrigatório", key="novo_numero_os")
            cliente_nome_form = st.text_input("Nome do Cliente", help="Obrigatório", key="novo_cliente_nome")
            consultor_nome_form = st.selectbox("Consultor", options=[""] + consultores_nomes, help="Obrigatório", key="novo_consultor_nome")
        
        with col2:
            modelo_nome_form = st.text_input("Nome do Modelo", help="Obrigatório", key="novo_modelo_nome")
            chassi_form = st.text_input("Chassi", help="Obrigatório", key="novo_chassi")
            data_abertura_form = st.date_input("Data de Abertura", datetime.today(), help="Obrigatório", key="novo_data_abertura")
            status_desc_form = st.text_input("Status (Ex: Aguardando Peça, Aprovado)", help="Obrigatório", key="novo_status_desc")
        
        with col3:
            descricao_servico_form = st.text_area("Descrição do Serviço", key="novo_descricao_servico")
            valor_liquido_str_form = st.text_input("Valor Líquido (use . ou , para decimal)", help="Ex: 123.45 ou 1.234,56", key="novo_valor_liquido")
        
        submitted = st.form_submit_button("Cadastrar OS")

        if submitted:
            if not all([numero_os.strip(), cliente_nome_form.strip(), modelo_nome_form.strip(), chassi_form.strip(),
                         data_abertura_form, consultor_nome_form, status_desc_form.strip()]):
                st.error("Por favor, preencha todos os campos obrigatórios.")
                st.stop()

            conn = conectar()
            cursor = conn.cursor()
            
            try:
                cliente_id = db_utils.get_or_create_cliente(cursor, cliente_nome_form.strip(), None, None)
                tipo_maquina_id = db_utils.get_or_create_tipo_maquina(cursor, "Trator") # Default "Trator"
                modelo_id = db_utils.get_or_create_modelo(cursor, modelo_nome_form.strip(), chassi_form.strip(), tipo_maquina_id)
                consultor_id = db_utils.get_consultor_id_by_name(cursor, consultor_nome_form)
                status_id = db_utils.get_or_create_status(cursor, status_desc_form.strip())

                if consultor_id is None:
                    st.error(f"Erro: Consultor '{consultor_nome_form}' não encontrado. Por favor, cadastre o consultor primeiro na página de Consultores.")
                    conn.close()
                    st.stop()
                
                tipo_os_default_value = "Garantia"

                valor_liquido_db = None
                if valor_liquido_str_form.strip():
                    try:
                        valor_limpo = valor_liquido_str_form.strip().replace('R$', '').replace('.', '').replace(',', '.')
                        valor_liquido_db = float(valor_limpo)
                    except ValueError:
                        st.error("Erro: 'Valor Líquido' inválido. Use um formato numérico válido (ex: 123.45 ou 1.234,56).")
                        conn.close()
                        st.stop()

                cursor.execute("""
                    INSERT INTO OrdemDeServico
                    (numero_os, tipo_os, cliente_id, modelo_id, consultor_id, status_id, descricao_servico, data_abertura, valor_liquido)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    numero_os.strip(), tipo_os_default_value, cliente_id, modelo_id, consultor_id,
                    status_id, descricao_servico_form.strip(), data_abertura_form.strftime('%Y-%m-%d'),
                    valor_liquido_db
                ))
                conn.commit()
                st.success(f"Ordem de Serviço Nº {numero_os.strip()} cadastrada com sucesso!")
                get_all_auxiliary_data.clear()
                st.rerun()
            
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: OrdemDeServico.numero_os" in str(e):
                    st.error(f"Erro: Já existe uma Ordem de Serviço com o número '{numero_os.strip()}'. Por favor, use um número diferente ou edite a OS existente.")
                else:
                    st.error(f"Erro de integridade ao cadastrar OS: {e}")
                conn.rollback()
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado ao cadastrar OS: {e}")
                conn.rollback()
            finally:
                conn.close()


    # --- Seção "ORDEM DE SERVIÇO EM ABERTO" ---
    st.subheader("📊 Ordens de Serviço em Aberto (Aguardando Faturamento)")

    conn_initial = conectar()
    query_os_aberto = """
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
        os.descricao_servico,
        os.cliente_id,
        os.modelo_id,
        os.consultor_id,
        os.status_id
    FROM OrdemDeServico os
    JOIN Cliente c ON os.cliente_id = c.id
    JOIN Modelo m ON os.modelo_id = m.id
    JOIN Consultor con ON os.consultor_id = con.id
    JOIN Status s ON os.status_id = s.id
    WHERE os.data_faturamento IS NULL
    """

    if st.session_state.usuario["permissao"] == "consultor":
        query_os_aberto += f" AND os.consultor_id = {st.session_state.usuario['id']}"
    
    query_os_aberto += " ORDER BY os.data_abertura DESC"
    
    df_ordens_aberto = pd.read_sql_query(query_os_aberto, conn_initial)
    conn_initial.close()

    for col in ['numero_os', 'tipo_os', 'cliente_nome', 'cliente_cpf', 'cliente_telefone',
                'status_descricao', 'modelo_nome', 'consultor_nome', 'modelo_chassi',
                'descricao_servico']:
        df_ordens_aberto[col] = df_ordens_aberto[col].apply(lambda x: str(x).strip() if pd.notna(x) else None)

    for col in ['data_abertura', 'data_faturamento', 'data_pagamento_fabrica']:
        df_ordens_aberto[col] = pd.to_datetime(df_ordens_aberto[col], errors='coerce')
        df_ordens_aberto[col] = df_ordens_aberto[col].dt.strftime('%d/%m/%Y')
        df_ordens_aberto[col] = df_ordens_aberto[col].fillna("")
    
    df_ordens_aberto['valor_liquido'] = df_ordens_aberto['valor_liquido'].apply(lambda x: f"{x:.2f}".replace('.', ',') if pd.notna(x) else "")
    
    if not df_ordens_aberto.empty:
        st.write("Edite 'Data Faturamento' e 'Data Pagamento Fábrica' para mover a OS para 'Faturadas'.")

        display_columns_aberto = [
            "numero_os", "tipo_os", "cliente_nome",
            "status_descricao", "modelo_nome", "consultor_nome", "modelo_chassi",
            "data_abertura", "valor_liquido", "data_faturamento", "data_pagamento_fabrica",
            "descricao_servico"
        ]

        column_config_dict_aberto = {
            "id": st.column_config.Column("ID", width="small", disabled=True),
            "numero_os": st.column_config.Column("N° O.S", disabled=True),
            "tipo_os": st.column_config.SelectboxColumn(
                "TIPO OS", options=["Garantia", "Cliente"], required=True,
                disabled=True if st.session_state.usuario["permissao"] == "consultor" else False
            ),
            "cliente_nome": st.column_config.Column("CLIENTE", disabled=True),
            "cliente_cpf": None,
            "cliente_telefone": None,
            "status_descricao": st.column_config.TextColumn("STATUS", disabled=False),
            "modelo_nome": st.column_config.Column("MODELO", disabled=True),
            "consultor_nome": st.column_config.Column("CONSULTOR", disabled=True),
            "modelo_chassi": st.column_config.Column("CHASSI", disabled=True),
            "data_abertura": st.column_config.Column("ABERTURA", disabled=True),
            "valor_liquido": st.column_config.TextColumn(
                "VALOR LÍQUIDO", disabled=True if st.session_state.usuario["permissao"] == "consultor" else False
            ),
            "data_faturamento": st.column_config.TextColumn("DATA FATURAMENTO"),
            "data_pagamento_fabrica": st.column_config.TextColumn("DATA PAGAMENTO FÁBRICA"),
            "descricao_servico": st.column_config.Column("SERVIÇO", disabled=False),
            "cliente_id": None, "modelo_id": None, "consultor_id": None, "status_id": None
        }

        edited_df_aberto = st.data_editor(
            df_ordens_aberto[display_columns_aberto],
            column_config=column_config_dict_aberto,
            num_rows="fixed",
            hide_index=True,
            key="os_aberto_data_editor"
        )

        if st.button("Salvar Alterações das OS em Aberto"):
            changes_made_overall = False 
            conn = conectar() 
            cursor = conn.cursor()

            original_df_reload_conn = conectar()
            original_df_reload = pd.read_sql_query(query_os_aberto, original_df_reload_conn)
            original_df_reload_conn.close()

            for col in ['data_abertura', 'data_faturamento', 'data_pagamento_fabrica']:
                original_df_reload[col] = pd.to_datetime(original_df_reload[col], errors='coerce').dt.date
                original_df_reload[col] = original_df_reload[col].apply(lambda x: None if pd.isna(x) else x)
            
            original_df_reload['valor_liquido'] = original_df_reload['valor_liquido'].apply(lambda x: float(str(x).replace(',', '.')) if pd.notna(x) else None)


            for idx, edited_row in edited_df_aberto.iterrows():
                original_row = original_df_reload[original_df_reload['numero_os'] == edited_row['numero_os']]

                if not original_row.empty:
                    original_row = original_row.iloc[0]
                    # CONVERTENDO O ID PARA INT AQUI, para evitar problemas com np.int64
                    os_id = int(original_row['id']) 

                    row_has_changes = False 
                    fields_to_update_os = {}

                    # 1. Status (TextColumn)
                    edited_status_desc = edited_row['status_descricao']
                    original_status_desc = original_row['status_descricao']
                    
                    if edited_status_desc != original_status_desc:
                        new_status_id = db_utils.get_or_create_status(cursor, edited_status_desc.strip())
                        fields_to_update_os['status_id'] = new_status_id
                        row_has_changes = True
                        print(f"DEBUG (OS {os_id}): Status alterado de '{original_status_desc}' para '{edited_status_desc}'. Novo status_id: {new_status_id}")

                    # 2. Data Faturamento (TextColumn -> Date)
                    edited_data_faturamento_str = edited_row['data_faturamento']
                    
                    parsed_edited_data_faturamento = None
                    if edited_data_faturamento_str and edited_data_faturamento_str.strip():
                        try:
                            parsed_edited_data_faturamento = datetime.strptime(edited_data_faturamento_str.strip(), '%d/%m/%Y').date()
                        except ValueError:
                            st.error(f"Erro no formato da Data Faturamento para OS {edited_row['numero_os']}. Use DD/MM/YYYY.")
                            conn.rollback() 
                            conn.close()
                            st.stop()
                    
                    if parsed_edited_data_faturamento != original_row['data_faturamento']:
                        fields_to_update_os['data_faturamento'] = parsed_edited_data_faturamento.strftime('%Y-%m-%d') if parsed_edited_data_faturamento is not None else None
                        row_has_changes = True
                        print(f"DEBUG (OS {os_id}): Data Faturamento alterada de '{original_row['data_faturamento']}' para '{parsed_edited_data_faturamento}'.")

                    # 3. Data Pagamento Fábrica (TextColumn -> Date)
                    edited_data_pagamento_fabrica_str = edited_row['data_pagamento_fabrica']

                    parsed_edited_data_pagamento_fabrica = None
                    if edited_data_pagamento_fabrica_str and edited_data_pagamento_fabrica_str.strip():
                        try:
                            parsed_edited_data_pagamento_fabrica = datetime.strptime(edited_data_pagamento_fabrica_str.strip(), '%d/%m/%Y').date()
                        except ValueError:
                            st.error(f"Erro no formato da Data Pagamento Fábrica para OS {edited_row['numero_os']}. Use DD/MM/YYYY.")
                            conn.rollback()
                            conn.close()
                            st.stop()

                    if parsed_edited_data_pagamento_fabrica != original_row['data_pagamento_fabrica']:
                        fields_to_update_os['data_pagamento_fabrica'] = parsed_edited_data_pagamento_fabrica.strftime('%Y-%m-%d') if parsed_edited_data_pagamento_fabrica is not None else None
                        row_has_changes = True
                        print(f"DEBUG (OS {os_id}): Data Pagamento Fábrica alterada de '{original_row['data_pagamento_fabrica']}' para '{parsed_edited_data_pagamento_fabrica}'.")

                    # 4. Descrição do Serviço (TextColumn)
                    edited_descricao_servico_val = edited_row['descricao_servico']
                    original_descricao_servico_val = original_row['descricao_servico']
                    if edited_descricao_servico_val != original_descricao_servico_val:
                        fields_to_update_os['descricao_servico'] = edited_descricao_servico_val.strip() if edited_descricao_servico_val else None
                        row_has_changes = True
                        print(f"DEBUG (OS {os_id}): Descrição Serviço alterada.")

                    # 5. Campos que APENAS o Supervisor pode editar
                    if st.session_state.usuario["permissao"] == "supervisor":
                        # Tipo OS
                        edited_tipo_os_val = edited_row['tipo_os']
                        original_tipo_os_val = original_row['tipo_os']
                        if edited_tipo_os_val != original_tipo_os_val:
                            fields_to_update_os['tipo_os'] = edited_tipo_os_val
                            row_has_changes = True
                            print(f"DEBUG (OS {os_id}): Tipo OS alterado de '{original_tipo_os_val}' para '{edited_tipo_os_val}'.")
                        
                        # Valor Líquido (TextColumn -> Float)
                        edited_valor_liquido_str = edited_row['valor_liquido']
                        
                        parsed_edited_valor_liquido = None
                        if edited_valor_liquido_str and edited_valor_liquido_str.strip():
                            try:
                                valor_limpo = edited_valor_liquido_str.strip().replace('R$', '').replace('.', '').replace(',', '.')
                                parsed_edited_valor_liquido = float(valor_limpo)
                            except ValueError:
                                st.error(f"Erro no formato do Valor Líquido para OS {edited_row['numero_os']}. Use um formato numérico válido (ex: 123.45 ou 1.234,56).")
                                conn.rollback()
                                conn.close()
                                st.stop()
                        
                        if parsed_edited_valor_liquido != original_row['valor_liquido']:
                            fields_to_update_os['valor_liquido'] = parsed_edited_valor_liquido
                            row_has_changes = True
                            print(f"DEBUG (OS {os_id}): Valor Líquido alterado de '{original_row['valor_liquido']}' para '{parsed_edited_valor_liquido}'.")
                    
                    # --- EXECUTE O UPDATE SE HOUVER ALTERAÇÕES DETECTADAS PARA ESTA LINHA ---
                    if row_has_changes:
                        set_clauses_os = [f"{k} = ?" for k in fields_to_update_os.keys()]
                        query_update_os_sql = f"UPDATE OrdemDeServico SET {', '.join(set_clauses_os)} WHERE id = ?"
                        params_update_os = list(fields_to_update_os.values()) + [os_id] # os_id já é int aqui
                        
                        print(f"DEBUG (OS {os_id}): Executando UPDATE principal: {query_update_os_sql} com parâmetros {params_update_os}")
                        try:
                            cursor.execute(query_update_os_sql, params_update_os)
                            print(f"DEBUG (OS {os_id}): UPDATE principal executado com sucesso. Rows affected by this execute: {cursor.rowcount}") # Adicionado para ver o impacto individual
                        except sqlite3.Error as e:
                            st.error(f"Erro no DB ao atualizar OS {edited_row['numero_os']}: {e}")
                            conn.rollback()
                            conn.close()
                            st.stop()
                        except Exception as e:
                            st.error(f"Erro inesperado ao atualizar OS {edited_row['numero_os']}: {e}")
                            conn.rollback()
                            conn.close()
                            st.stop()


                        # --- Lógica de Transição para Faturada ---
                        status_faturada_id = status_map.get("Faturada")
                        if status_faturada_id is None:
                            # Esta parte pode ser o motivo do conflito de IDs.
                            # Se 'Faturada' foi digitado e não existia, get_or_create_status irá criá-lo.
                            # É crucial que essa função seja robusta e não crie duplicatas.
                            status_faturada_id = db_utils.get_or_create_status(cursor, "Faturada")
                            status_map["Faturada"] = status_faturada_id # Garante que o status_map está atualizado
                            print(f"DEBUG: Status 'Faturada' criado (ou obtido) com ID: {status_faturada_id}. (Pode ocorrer mais de uma vez se não estiver no cache)")
                            
                        # Verifica se o status *digitado* é 'Faturada' E se a data de faturamento *foi preenchida*
                        if edited_status_desc and edited_status_desc.lower() == 'faturada' and parsed_edited_data_faturamento is not None:
                            current_status_id_in_transaction = fields_to_update_os.get('status_id', original_row['status_id'])
                            
                            # Se o status da OS no DB (após o update principal) ainda não for 'Faturada', força a atualização
                            if current_status_id_in_transaction != status_faturada_id:
                                print(f"DEBUG (OS {os_id}): Status atual na transação ({current_status_id_in_transaction}) diferente de 'Faturada' ({status_faturada_id}). Forçando atualização.")
                                try:
                                    cursor.execute("UPDATE OrdemDeServico SET status_id = ? WHERE id = ?", (status_faturada_id, os_id))
                                    changes_made_overall = True 
                                    st.success(f"OS {edited_row['numero_os']} marcada como 'Faturada' e movida para a aba 'Faturadas'!")
                                    print(f"DEBUG (OS {os_id}): Status FORÇADO para 'Faturada' com sucesso. Rows affected: {cursor.rowcount}")
                                except sqlite3.Error as e:
                                    st.error(f"Erro no DB ao forçar status para OS {edited_row['numero_os']}: {e}")
                                    conn.rollback()
                                    conn.close()
                                    st.stop()
                                except Exception as e:
                                    st.error(f"Erro inesperado ao forçar status para OS {edited_row['numero_os']}: {e}")
                                    conn.rollback()
                                    conn.close()
                                    st.stop()
                            else:
                                st.success(f"OS {edited_row['numero_os']} marcada como 'Faturada' e movida para a aba 'Faturadas'!")
                                changes_made_overall = True 
                                print(f"DEBUG (OS {os_id}): Status já era 'Faturada' ou foi atualizado no UP principal. Confirmando sucesso.")

                        elif row_has_changes: 
                            st.info(f"OS {edited_row['numero_os']} atualizada.")
                            changes_made_overall = True 

                    else:
                        st.info(f"Nenhuma alteração detectada para OS {edited_row['numero_os']}.")
                else:
                    st.warning(f"OS {edited_row['numero_os']} não encontrada no banco de dados original para atualização.")

            print(f"DEBUG: Tentando commit final. changes_made_overall = {changes_made_overall}")
            conn.commit()
            #cursor.rowcount após commit() pode não ser o total de linhas modificadas na transação inteira,
            # mas sim da última operação. O importante é o commit ter ocorrido sem erro.
            print(f"DEBUG: Commit final realizado.") 
            
            if changes_made_overall:
                get_all_auxiliary_data.clear()
                print("DEBUG: Cache limpo. Chamando st.rerun()")
                st.rerun()
            else:
                st.info("Nenhuma alteração a ser salva.")
                
            conn.close()
                
    else:
        st.info("Nenhuma Ordem de Serviço em Aberto. Cadastre uma nova OS ou verifique as OSs faturadas.")

    # --- Lógica para Deletar Ordens de Serviço ---
    st.markdown("---")
    st.subheader("🗑️ Excluir Ordens de Serviço")
    
    if st.session_state.usuario["permissao"] == "supervisor":
        conn_delete = conectar()
        query_os_aberto_delete = """
        SELECT
            os.id, os.numero_os
        FROM OrdemDeServico os
        WHERE os.data_faturamento IS NULL
        """
        if st.session_state.usuario["permissao"] == "consultor":
            query_os_aberto_delete += f" AND os.consultor_id = {st.session_state.usuario['id']}"
        
        df_ordens_aberto_for_delete = pd.read_sql_query(query_os_aberto_delete, conn_delete)
        conn_delete.close()

        if not df_ordens_aberto_for_delete.empty:
            os_para_excluir_nomes = st.multiselect(
                "Selecione o(s) número(s) da OS para excluir (apenas em aberto):",
                df_ordens_aberto_for_delete['numero_os'].tolist(),
                key="multiselect_delete_os"
            )

            if st.button("Excluir OSs Selecionadas", key="delete_os_button"):
                if os_para_excluir_nomes:
                    conn = conectar()
                    deleted_count = 0
                    for os_num in os_para_excluir_nomes:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM OrdemDeServico WHERE numero_os = ?", (os_num,))
                        os_id_to_delete = cursor.fetchone()
                        
                        if os_id_to_delete:
                            if db_utils.delete_record(conn, "OrdemDeServico", os_id_to_delete[0]):
                                deleted_count += 1
                            else:
                                st.error(f"Falha ao excluir OS {os_num}.")
                        else:
                            st.warning(f"OS {os_num} não encontrada no banco de dados para exclusão.")
                    
                    conn.close()
                    if deleted_count > 0:
                        st.success(f"{deleted_count} Ordem(ns) de Serviço excluída(s) com sucesso!")
                        get_all_auxiliary_data.clear()
                        st.rerun()
                    else:
                        st.info("Nenhuma OS foi excluída.")
                else:
                    st.warning("Selecione pelo menos uma Ordem de Serviço para excluir.")
        else:
            st.info("Nenhuma Ordem de Serviço em aberto para excluir.")
    else:
        st.info("Apenas supervisores podem excluir Ordens de Serviço.")