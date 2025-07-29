import streamlit as st
from controllers import auth
import os

# Importar as funções de cada página. Certifique-se que seus arquivos na pasta 'app_pages/' NÃO têm números no nome.
# E que a pasta se chama 'app_pages'
import app_pages.Dashboard as dashboard_page
import app_pages.Ordens as ordens_page
import app_pages.Clientes as clientes_page
import app_pages.Consultores as consultores_page
import app_pages.Config as config_page
import app_pages.Maquinas as maquinas_page
import app_pages.Faturadas as faturadas_page



# st.set_page_config DEVE SER O PRIMEIRO COMANDO Streamlit!
st.set_page_config(page_title="Gestão de Ordens de Serviço", layout="wide", initial_sidebar_state="auto")

# --- REMOVIDO: Bloco de carregamento de CSS customizado e imagem de fundo ---

# Inicializa o estado de login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario = None
    st.session_state.current_page = "📊 Dashboard Geral" # Página inicial padrão após login


# Se não estiver logado, mostra apenas a tela de login CENTRALIZADA
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.write("") # Espaços em branco
        st.write("")
        
        # --- CARD ESTILIZADO PARA LOGO E LOGIN ---
        st.markdown(
            """
            <div style="
                background-color: #2E2E2E;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            ">
            """,
            unsafe_allow_html=True
        )

        # --- LOGO NA TELA DE LOGIN (CENTRALIZADA, MENOR E NO TOPO DO CARD) ---
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_principal.jpg")
            
            if os.path.exists(logo_path):
                st.image(logo_path, width=200)
            else:
                st.warning("Arquivo da logo principal não encontrado em 'assets/logo_principal.jpg'.")
        except Exception as e:
            st.error(f"Erro ao carregar a logo na tela de login: {e}")
        # --- FIM LOGO LOGIN ---

        st.write("")
        
        auth.login()

        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Se estiver logado, mostra o menu lateral e o conteúdo da página
    st.sidebar.title(f"Bem-vindo, {st.session_state.usuario['nome']}!")
    st.sidebar.write(f"Permissão: {st.session_state.usuario['permissao'].capitalize()}")

    # Opções de navegação do menu principal
    menu_options = {
        "📊 Dashboard Geral": dashboard_page.app,
        "📝 Gerenciar Ordens de Serviço": ordens_page.app, # Página de cadastro de novas OS        
        "✅ Faturadas": faturadas_page.app,
        "👤 Clientes": clientes_page.app,
        "🧑‍💼 Consultores": consultores_page.app,
        "🔧 Máquinas": maquinas_page.app,
        "⚙️ Configurações": config_page.app,
    }

    # Restringe acesso a certas páginas para consultores
    if st.session_state.usuario["permissao"] == "consultor":
        if "🧑‍💼 Consultores" in menu_options:
            del menu_options["🧑‍💼 Consultores"]

    # Permite selecionar a página no sidebar
    selected_page_title = st.sidebar.radio("Navegar", list(menu_options.keys()),
                                        index=list(menu_options.keys()).index(st.session_state.current_page)
                                        if st.session_state.current_page in menu_options else 0)

    # LOGO NA BARRA LATERAL PARA OUTRAS PÁGINAS
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_principal.jpg")
        
        if os.path.exists(logo_path):
            st.sidebar.image(logo_path, width=80)
            st.sidebar.markdown("---")
        else:
            st.sidebar.warning("Arquivo da logo principal não encontrado em 'assets/logo_principal.jpg'.")
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar a logo na barra lateral: {e}")

    # Botão de Logout no final do sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("Sair"):
        auth.logout()

    # Exibir a página selecionada
    st.session_state.current_page = selected_page_title
    menu_options[selected_page_title]()