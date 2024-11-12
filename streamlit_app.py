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

def get_address_from_private_key(private_key):
    account = Web3().eth.account.from_key(private_key)
    return account.address

def download_link_pdf(pdf_content, filename="contrato.pdf"):
    b64 = base64.b64encode(pdf_content).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Baixar Contrato</a>'


if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

def show_login_page():
    st.title("Login")
    login = st.text_input("Login", key="unique_login_key")

    if st.button("Entrar"):
        if not login:
            st.error("Login é obrigatório.")
        else:
            login_data = {"login": login}
            st.write(f"Login enviado: {login_data}")  # Verifique o valor de login
            response, success = api_post("api/login/", login_data)
            if success:
                st.success("Login realizado com sucesso!")
                st.session_state["user_id"] = response["user_id"]
                st.session_state["is_logged_in"] = True
                st.experimental_rerun()
            else:
                st.error("Erro ao fazer login: Usuário não encontrado.")

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
    
def api_get(endpoint):
    try:
        response = requests.get(f"{DJANGO_API_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json(), True
        else:
            try:
                return response.json(), False
            except ValueError:
                return response.text, False
    except requests.ConnectionError:
        return "Erro de conexão com a API.", False

def fetch_contracts():
    data, success = api_get("api/contracts/")
    if success:
        return data
    else:
        return []

if not st.session_state["is_logged_in"]:
    show_login_page()
else:
    # Menu lateral e páginas do aplicativo para o usuário logado
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
        
        # Campos para criação de contrato
        landlord = st.text_input("Endereço do Locador")
        tenant = st.text_input("Endereço do Inquilino")
        rent_amount = st.number_input("Valor do Aluguel (Wei)", min_value=0, step=1)
        deposit_amount = st.number_input("Valor do Depósito (Wei)", min_value=0, step=1)
        start_date = st.date_input("Data de Início do Contrato")
        end_date = st.date_input("Data de Término do Contrato")
        contract_duration = st.number_input("Duração do Contrato (Meses)", min_value=1, step=1)
        private_key = st.text_input("Chave Privada (Locador)", type="password")

        if st.button("Criar Contrato"):
            if not landlord or not tenant:
                st.error("Endereços do locador e inquilino são obrigatórios.")
            elif not private_key:
                st.error("Chave privada do locador é obrigatória.")
            else:
                contract_data = {
                    "landlord": landlord,
                    "tenant": tenant,
                    "rent_amount": rent_amount,
                    "deposit_amount": deposit_amount,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "contract_duration": contract_duration,
                    "private_key": private_key
                }

                with st.spinner("Processando..."):
                    result, success = api_post("api/create/", contract_data)
                    if success:
                        st.success(f"Contrato criado com sucesso!\nEndereço do Contrato: {result['contract_address']}\nTx Hash: {result['tx_hash']}")
                    else:
                        st.error(f"Erro ao criar contrato: {result}")

    elif page == "Assinar Contrato":
        st.title("Assinar Contrato Inteligente")
        
        contract_id = st.text_input("ID do Contrato")
        private_key = st.text_input("Chave Privada", type="password")
        user_type = st.selectbox("Tipo de Usuário", ["Locador", "Inquilino"])
        
        user_type_mapped = "landlord" if user_type == "Locador" else "tenant"

        if st.button("Assinar Contrato"):
            if not contract_id:
                st.error("ID do contrato é obrigatório.")
            elif not private_key:
                st.error("Chave privada é obrigatória.")
            else:
                try:
                    user_address = get_address_from_private_key(private_key)
                    st.write(f"Endereço derivado da chave privada: {user_address}")
                    
                    signature_data = {
                        "private_key": private_key,
                        "user_type": user_type_mapped,
                        "user_address": user_address
                    }

                    with st.spinner("Processando..."):
                        result, success = api_post(f"api/contracts/{contract_id}/sign/", signature_data)

                        if success:
                            st.success(f"Contrato assinado com sucesso!\nTx Hash: {result['tx_hash']}\nStatus: {result['status']}")
                        else:
                            st.error(f"Erro ao assinar contrato: {result}")
                except Exception as e:
                    st.error(f"Erro ao derivar endereço da chave privada: {str(e)}")

    elif page == "Registrar Pagamento":
        st.title("Registrar Pagamento")
        
        contract_id = st.text_input("ID do Contrato")
        private_key = st.text_input("Chave Privada (Inquilino)", type="password")
        payment_type = st.selectbox("Tipo de Pagamento", ["Aluguel", "Depósito"])
        amount = st.number_input("Valor do Pagamento (ETH)", min_value=0.0, step=0.01)

        if st.button("Registrar Pagamento"):
            if not contract_id:
                st.error("ID do contrato é obrigatório.")
            elif not private_key:
                st.error("Chave privada é obrigatória.")
            elif amount <= 0:
                st.error("Valor do pagamento deve ser maior que zero.")
            else:
                payment_data = {
                    "private_key": private_key,
                    "payment_type": payment_type,
                    "amount": amount
                }
                with st.spinner("Processando..."):
                    result, success = api_post(f"api/contracts/{contract_id}/register_payment/", payment_data)
                    if success:
                        st.success(f"Pagamento de {payment_type} registrado com sucesso!\nTx Hash: {result['tx_hash']}")
                    else:
                        st.error(f"Erro ao registrar pagamento: {result}")

    elif page == "Visualizar Contratos":
        st.title("Lista de Contratos de Aluguel")
        contracts = fetch_contracts()

        if contracts:
            for contract in contracts:
                st.markdown(f"""
                ***Contrato {contract['id']}***
                - **Locador**: {contract['landlord']}  
                - **Inquilino**: {contract['tenant']}  
                - **Valor do Aluguel**: {contract['rent_amount']} ETH  
                - **Valor do Depósito**: {contract['deposit_amount']} ETH  
                - **Endereço do Contrato**: {contract['contract_address']}  
                - **Status**: {contract['status']}  
                - **Data de Criação**: {contract['created_at']}
                """)
                st.markdown("---")

                pdf_content = gerar_pdf_contrato(contract)
                st.download_button(
                    label="Clique para baixar o PDF",
                    data=pdf_content,
                    file_name=f"contrato_{contract['id']}.pdf",
                    mime="application/pdf",
                    key=f"download_{contract['id']}"
                )
        else:
            st.write("Nenhum contrato encontrado.")

    elif page == "Encerrar Contrato":
        st.title("Encerrar Contrato Inteligente")
        contract_id = st.text_input("ID do Contrato")
        private_key = st.text_input("Chave Privada (Locador)", type="password")

        if st.button("Encerrar Contrato"):
            if not contract_id:
                st.error("ID do contrato é obrigatório.")
            elif not private_key:
                st.error("Chave privada é obrigatória.")
            else:
                termination_data = {"private_key": private_key}
                with st.spinner("Processando..."):
                    result, success = api_post(f"api/contracts/{contract_id}/terminate/", termination_data)
                    if success:
                        st.success(f"Contrato encerrado com sucesso!\nTx Hash: {result['tx_hash']}")
                    else:
                        st.error(f"Erro ao encerrar contrato: {result}")

    elif page == "Simular Passagem de Tempo":
        st.title("Simular Passagem de Tempo")
        contract_id = st.text_input("ID do Contrato")
        data_simulada = st.date_input("Data Simulada", value=datetime.date.today())
        private_key = st.text_input("Chave Privada (Locador)", type="password")

        if st.button("Avançar Tempo"):
            if not contract_id:
                st.error("ID do contrato é obrigatório.")
            elif not private_key:
                st.error("Chave privada é obrigatória.")
            elif not data_simulada:
                st.error("A data é obrigatória.")
            else:
                simulation_data = {
                    "simulated_date": data_simulada.strftime('%Y-%m-%d'),
                    "private_key": private_key
                }
                with st.spinner("Processando..."):
                    result, success = api_post(f"api/contracts/{contract_id}/simular_tempo/", simulation_data)
                    if success:
                        st.success(f"Simulação completada!\nTx Hash: {result['tx_hash']}\nNova data de término: {result['end_date']}")
                    else:
                        st.error(f"Erro ao avançar o tempo: {result}")

# Função para logout
if st.sidebar.button("Logout"):
    st.session_state["is_logged_in"] = False
    st.experimental_rerun()  # Atualiza a página após o logout
