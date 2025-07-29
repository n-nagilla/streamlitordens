import streamlit as st
import sqlite3
import os

def conectar():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "..", "database", "db.sqlite3")
    return sqlite3.connect(db_path)

def login():
    st.title("Login")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, permissao FROM Consultor WHERE email = ? AND senha = ?", (email, senha))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            st.session_state.logged_in = True
            st.session_state.usuario = {
                "id": resultado[0],
                "nome": resultado[1],
                "permissao": resultado[2]
            }
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.usuario = None
    st.rerun()