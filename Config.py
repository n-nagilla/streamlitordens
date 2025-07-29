import streamlit as st
import sqlite3
from controllers.auth import conectar

def app(): # <--- Todo o código da página deve estar aqui dentro
    st.title("⚙️ Configurações do Perfil")

    st.subheader("Visualizar e Editar Meu Perfil")

    usuario = st.session_state.get("usuario", None)
    if not usuario:
        st.warning("Nenhum usuário logado. Faça login para ver e editar seu perfil.")
        return # Sai da função se não houver usuário

    conn = conectar()
    cursor = conn.cursor()

    # Recuperar os dados mais recentes do usuário do banco de dados
    cursor.execute("SELECT id, nome, email, permissao FROM Consultor WHERE id = ?", (usuario['id'],))
    dados_usuario_db = cursor.fetchone()
    
    if not dados_usuario_db:
        st.error("Seu perfil não foi encontrado no banco de dados. Tente fazer login novamente.")
        conn.close()
        return

    # Extrair dados para pré-preencher o formulário
    usuario_id_db, nome_db, email_db, permissao_db = dados_usuario_db

    with st.form("form_editar_perfil", clear_on_submit=False): # clear_on_submit=False para manter os dados no form
        st.write("Edite suas informações abaixo:")
        
        novo_nome = st.text_input("Nome", value=nome_db, key="edit_nome")
        novo_email = st.text_input("E-mail", value=email_db, key="edit_email")
        
        # Campo para alterar senha (opcional)
        st.write("---")
        st.write("#### Alterar Senha")
        nova_senha = st.text_input("Nova Senha", type="password", key="edit_nova_senha")
        confirmar_nova_senha = st.text_input("Confirmar Nova Senha", type="password", key="edit_confirmar_nova_senha")

        submitted = st.form_submit_button("Salvar Alterações")

        if submitted:
            changes_made = False
            fields_to_update = {}

            # Checar alteração de nome
            if novo_nome != nome_db:
                fields_to_update['nome'] = novo_nome
                changes_made = True
            
            # Checar alteração de email
            if novo_email != email_db:
                fields_to_update['email'] = novo_email
                changes_made = True
            
            # Checar alteração de senha
            if nova_senha: # Se o campo de nova senha não estiver vazio
                if nova_senha != confirmar_nova_senha:
                    st.error("Erro: Nova senha e confirmação de senha não coincidem.")
                    conn.close()
                    st.stop()
                else:
                    fields_to_update['senha'] = nova_senha # Senha não criptografada
                    changes_made = True

            if not changes_made:
                st.info("Nenhuma alteração detectada para salvar.")
                conn.close()
                st.stop()

            # Executar o UPDATE
            try:
                set_clauses = [f"{k} = ?" for k in fields_to_update.keys()]
                query_update = f"UPDATE Consultor SET {', '.join(set_clauses)} WHERE id = ?"
                params_update = list(fields_to_update.values()) + [usuario_id_db]
                
                cursor.execute(query_update, params_update)
                conn.commit()
                st.success("Perfil atualizado com sucesso! Recarregando...")

                # Atualizar st.session_state.usuario para refletir as mudanças
                st.session_state.usuario['nome'] = novo_nome
                st.session_state.usuario['email'] = novo_email
                # Senha não é armazenada diretamente no session_state, então não precisa atualizar

                conn.close()
                st.rerun() # Recarrega a página para exibir as alterações
            
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Consultor.email" in str(e):
                    st.error("Erro: Este e-mail já está em uso por outro consultor.")
                else:
                    st.error(f"Erro de integridade ao atualizar perfil: {e}")
                conn.rollback()
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado ao atualizar perfil: {e}")
                conn.rollback()
            finally:
                conn.close()
    
    st.markdown("---")
    st.write(f"**Permissão Atual:** {permissao_db.capitalize()}")
    if permissao_db == "consultor":
        st.info("Para alterar sua permissão (para Supervisor), entre em contato com um Supervisor.")

    conn.close()