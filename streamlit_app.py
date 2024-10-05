import streamlit as st # type:ignore
import requests # type:ignore
import os
import json
from dotenv import load_dotenv # type:ignore
from web3 import Web3 # type:ignore

load_dotenv()

DJANGO_API_URL = os.getenv("DJANGO_API_URL")  # Exemplo: "http://localhost:8000/"

def get_address_from_private_key(private_key):
    account = Web3().eth.account.from_key(private_key)
    return account.address

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
        response = requests.get(f"{DJANGO_API_URL}{endpoint}")
        if response.status_code == 200:
            return response.json(), True
        else:
            try:
                return response.json(), False
            except ValueError:
                return response.text, False
    except requests.ConnectionError:
        return "Erro de conexão com a API.", False

# Função para buscar contratos
def fetch_contracts():
    data, success = api_get("api/contracts/")
    if success:
        return data
    else:
        return []

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
    rent_amount = st.number_input("Valor do Aluguel (ETH)", min_value=0.0, step=0.01)
    deposit_amount = st.number_input("Valor do Depósito (ETH)", min_value=0.0, step=0.01)
    private_key = st.text_input("Chave Privada do Locador", type="password")

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
                "private_key": private_key
            }
            with st.spinner("Processando..."):
                result, success = api_post("api/create/", contract_data)
                if success:
                    st.success(f"Contrato criado com sucesso!\nEndereço do Contrato: {result['contract_address']}\nTx Hash: {result['tx_hash']}")
                else:
                    st.error(f"Erro ao criar contrato: {result}")

if page == "Assinar Contrato":
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
            # Derivar o endereço da chave privada
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
                        st.error(f"Erro ao assinar contrato: {result.get('error', result)}")
            except Exception as e:
                st.error(f"Erro ao derivar endereço da chave privada: {str(e)}")

# Página de Executar Contrato
if page == "Executar Contrato":
    st.title("Executar Contrato Inteligente")
    
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")

    if st.button("Executar Contrato"):
        if not contract_id:
            st.error("ID do contrato é obrigatório.")
        elif not private_key:
            st.error("Chave privada é obrigatória.")
        else:
            execution_data = {
                "private_key": private_key
            }
            with st.spinner("Processando..."):
                result, success = api_post(f"api/contracts/{contract_id}/execute/", execution_data)
                if success:
                    st.success(f"Contrato executado com sucesso!\nTx Hash: {result['tx_hash']}")
                else:
                    st.error(f"Erro ao executar contrato: {result}")

# Página de Registrar Pagamento
if page == "Registrar Pagamento":
    st.title("Registrar Pagamento")
    
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")
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

# Página de Visualizar Contratos
if page == "Visualizar Contratos":
    st.title("Lista de Contratos de Aluguel")
    contracts = fetch_contracts()

    if contracts:
        for contract in contracts:
            st.markdown(f"""
            **Contrato {contract['id']}**  
            - **Locador**: {contract['landlord']}  
            - **Inquilino**: {contract['tenant']}  
            - **Valor do Aluguel**: {contract['rent_amount']} ETH  
            - **Valor do Depósito**: {contract['deposit_amount']} ETH  
            - **Endereço do Contrato**: {contract['contract_address']}  
            - **Status**: {contract['status']}  
            - **Data de Criação**: {contract['created_at']}
            """)
            st.markdown("---")

            # Buscar eventos relacionados ao contrato
            events, success = api_get(f"api/contracts/{contract['id']}/events/")
            if success and events:
                st.subheader("Eventos")
                for event in events:
                    st.markdown(f"""
                    - **Tipo**: {event['event_type']}  
                    - **Tx Hash**: {event['tx_hash']}  
                    - **De**: {event['from_address']}  
                    - **Detalhes**: {json.dumps(event['event_data'], indent=2)}
                    """)
            else:
                st.write("Nenhum evento encontrado para este contrato.")

            st.markdown("### ")
    else:
        st.write("Nenhum contrato encontrado.")

# Página de Encerrar Contrato
if page == "Encerrar Contrato":
    st.title("Encerrar Contrato Inteligente")

    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")

    if st.button("Encerrar Contrato"):
        if not contract_id:
            st.error("ID do contrato é obrigatório.")
        elif not private_key:
            st.error("Chave privada é obrigatória.")
        else:
            termination_data = {
                "private_key": private_key
            }
            with st.spinner("Processando..."):
                result, success = api_post(f"api/contracts/{contract_id}/terminate/", termination_data)
                if success:
                    st.success(f"Contrato encerrado com sucesso!\nTx Hash: {result['tx_hash']}")
                else:
                    st.error(f"Erro ao encerrar contrato: {result}")
