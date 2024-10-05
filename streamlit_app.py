import streamlit as st
import requests
import web3
import os

from dotenv import load_dotenv

load_dotenv()

DJANGO_API_URL = os.getenv("DJANGO_API_URL")

def api_post(endpoint, data):
    try:
        response = requests.post(f"{DJANGO_API_URL}{endpoint}", json=data)
        if response.status_code == 200 or response.status_code == 201:
            return response.json(), True
        else:
            return response.text, False
    except requests.ConnectionError:
        return "Erro de conexão com a API.", False

def api_get(endpoint):
    try:
        response = requests.get(f"{DJANGO_API_URL}{endpoint}")
        if response.status_code == 200:
            return response.json(), True
        else:
            return response.text, False
    except requests.ConnectionError:
        return "Erro de conexão com a API.", False

# Função para buscar contratos
def fetch_contracts():
    return api_get("api/contracts/")[0]

# Menu de navegação
st.sidebar.title("Gestão de Contratos Inteligentes")
page = st.sidebar.selectbox("Selecione a página",
                        ["Criar Contrato",
                         "Assinar Contrato",
                         "Executar Contrato",
                         "Registrar Pagamento",
                         "Visualizar Contratos",
                         "Encerrar Contrato"])

# Página de Criar Contrato
if page == "Criar Contrato":
    st.title("Criar Novo Contrato")
    
    landlord = st.text_input("Endereço do Locador")
    tenant = st.text_input("Endereço do Inquilino")
    rent_amount = st.number_input("Valor do Aluguel", min_value=0.0, step=0.01)
    deposit_amount = st.number_input("Valor do Depósito", min_value=0.0, step=0.01)
    private_key = st.text_input("Chave Privada do Locador", type="password")

    if st.button("Criar Contrato"):
        contract_data = {
            "landlord": landlord,
            "tenant": tenant,
            "rent_amount": rent_amount,
            "deposit_amount": deposit_amount,
            "private_key": private_key
        }
        with st.spinner("Processando..."):
            result, success = api_post("api/create_contract/", contract_data)
            if success:
                st.success("Contrato criado com sucesso!")
            else:
                st.error(f"Erro ao criar contrato: {result}")

# Página de Assinar Contrato
if page == "Assinar Contrato":
    st.title("Assinar Contrato Inteligente")
    
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")
    user_type = st.selectbox("Tipo de Usuário", ["Locador", "Inquilino"])
    
    user_type_mapped = "landlord" if user_type == "Locador" else "tenant"

    if st.button("Assinar Contrato"):
        signature_data = {
            "contract_id": contract_id,
            "private_key": private_key,
            "user_type": user_type_mapped.lower()
        }
        with st.spinner("Processando..."):
            result, success = api_post(f"api/contracts/{contract_id}/sign/", signature_data)
            if success:
                st.success("Contrato assinado com sucesso!")
            else:
                st.error(f"Erro ao assinar contrato: {result}")

# Página de Executar Contrato
if page == "Executar Contrato":
    st.title("Executar Contrato Inteligente")
    
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")

    if st.button("Executar Contrato"):
        execution_data = {
            "contract_id": contract_id,
            "private_key": private_key
        }
        with st.spinner("Processando..."):
            result, success = api_post(f"api/contracts/{contract_id}/execute/", execution_data)
            if success:
                st.success("Contrato executado com sucesso!")
            else:
                st.error(f"Erro ao executar contrato: {result}")

# Página de Registrar Pagamento
if page == "Registrar Pagamento":
    st.title("Registrar Pagamento")
    
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")
    payment_type = st.selectbox("Tipo de Pagamento", ["Aluguel", "Depósito"])
    amount = st.number_input("Valor do Pagamento", min_value=0.0, step=0.01)

    if st.button("Registrar Pagamento"):
        payment_data = {
            "private_key": private_key,
            "payment_type": payment_type,
            "amount": amount
        }
        with st.spinner("Processando..."):
            result, success = api_post(f"api/contracts/{contract_id}/register_payment/", payment_data)
            if success:
                st.success(f"Pagamento de {payment_type} registrado com sucesso!")
            else:
                st.error(f"Erro ao registrar pagamento: {result}")

# Página de Visualizar Contratos
if page == "Visualizar Contratos":
    st.title("Lista de Contratos de Aluguel")
    contracts = fetch_contracts()

    if contracts:
        for contract in contracts:
            st.markdown(f"""
            **Contrato de {contract['landlord']} para {contract['tenant']}**  
            - Valor do Aluguel: {contract['rent_amount']}  
            - Valor do Depósito: {contract['deposit_amount']}  
            - Endereço do Contrato: {contract['contract_address']}  
            - Data de Criação: {contract['created_at']}
            """)
            st.markdown("---")
            payments, success = api_get(f"api/contracts/{contract['id']}/payments/")
            if success:
                for payment in payments:
                    st.write(f"Pagamento: {payment['payment_type']} de {payment['amount']} em {payment['payment_date']}")
            termination, success = api_get(f"api/contracts/{contract['id']}/termination/")
            if success:
                st.write(f"Contrato Encerrado em: {termination['termination_date']} por {termination['terminated_by']}")
            st.markdown("---")
    else:
        st.write("Nenhum contrato encontrado.")

# Página de Encerrar Contrato
if page == "Encerrar Contrato":
    st.title("Encerrar Contrato Inteligente")

    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")

    if st.button("Encerrar Contrato"):
        termination_data = {
            "contract_id": contract_id,
            "private_key": private_key
        }
        with st.spinner("Processando..."):
            result, success = api_post(f"api/contracts/{contract_id}/terminate/", termination_data)
            if success:
                st.success("Contrato encerrado com sucesso!")
            else:
                st.error(f"Erro ao encerrar contrato: {result}")
