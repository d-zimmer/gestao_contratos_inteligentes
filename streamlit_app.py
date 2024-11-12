import streamlit as st # type:ignore
import requests # type:ignore
import os
import base64
import datetime
from dotenv import load_dotenv # type:ignore
from web3 import Web3 # type:ignore
from scripts.gerar_pdf_contrato import gerar_pdf_contrato

st.set_page_config(
    page_title="Gestão de Contratos",
    layout="centered",
    page_icon="scripts/flaticon.png"
)

load_dotenv()

DJANGO_API_URL = "http://gestaocontratos.brazilsouth.cloudapp.azure.com/"

# Verifique se o usuário está logado
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

# Função para exibir a página de login
def show_login_page():
    st.title("Login")
    nome_completo = st.text_input("Nome Completo")
    private_key = st.text_input("Chave Privada", type="password")

    if st.button("Entrar"):
        if not nome_completo or not private_key:
            st.error("Nome completo e chave privada são obrigatórios.")
        else:
            login_data = {"nome_completo": nome_completo, "private_key": private_key}
            user_data, success = api_post("api/login/", login_data)
            if success:
                st.success("Login realizado com sucesso!")
                # Armazene os dados do usuário na sessão
                st.session_state["user_data"] = user_data
                st.session_state["is_logged_in"] = True
                st.experimental_rerun()  # Atualiza a página após o login
            else:
                st.error("Erro ao fazer login.")

# Função para chamada da API POST
def api_post(endpoint, data):
    try:
        response = requests.post(f"{DJANGO_API_URL}{endpoint}", json=data)
        if response.status_code in [200, 201]:
            return response.json(), True
        else:
            try:
                return response.json(), False
            except ValueError:
                return response.text, False
    except requests.ConnectionError:
        return "Erro de conexão com a API.", False

# Se o usuário não estiver logado, exiba apenas a página de login
if not st.session_state["is_logged_in"]:
    show_login_page()
else:
    # Menu lateral e páginas do aplicativo
    st.sidebar.title("Gestão de Contratos Inteligentes")
    page = st.sidebar.selectbox("Selecione a página",
                                ["Criar Contrato",
                                 "Assinar Contrato",
                                 "Registrar Pagamento",
                                 "Visualizar Contratos",
                                 "Encerrar Contrato",
                                 "Simular Passagem de Tempo"])

    if page == "Criar Contrato":
        st.title("Criar Novo Contrato")
        # Seu código para criar contrato...

    elif page == "Assinar Contrato":
        st.title("Assinar Contrato Inteligente")
        # Seu código para assinar contrato...

    elif page == "Registrar Pagamento":
        st.title("Registrar Pagamento")
        # Seu código para registrar pagamento...

    elif page == "Visualizar Contratos":
        st.title("Lista de Contratos de Aluguel")
        # Seu código para visualizar contratos...

    elif page == "Encerrar Contrato":
        st.title("Encerrar Contrato Inteligente")
        # Seu código para encerrar contrato...

    elif page == "Simular Passagem de Tempo":
        st.title("Simular Passagem de Tempo")
        # Seu código para simular passagem de tempo...

# Função para logout
if st.sidebar.button("Logout"):
    st.session_state["is_logged_in"] = False
    st.experimental_rerun()  # Atualiza a página após o logout
