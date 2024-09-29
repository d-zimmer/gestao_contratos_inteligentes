import streamlit as st
import requests

# Defina o URL da API Django
DJANGO_API_URL = "http://localhost:8000/api/"

# Função para buscar contratos da API Django
def fetch_contracts():
    response = requests.get(f"{DJANGO_API_URL}contracts/")
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Menu de navegação para páginas diferentes
st.sidebar.title("Gestão de Contratos Inteligentes")
page = st.sidebar.radio("Ir para", ["Criar Contrato", "Assinar Contrato", "Executar Contrato", "Registrar Pagamento", "Visualizar Contratos", "Encerrar Contrato"])

# Página para criar contratos
if page == "Criar Contrato":
    st.title("Criar Novo Contrato")

    # Campos de entrada para o contrato
    landlord = st.text_input("Endereço do Locador")
    tenant = st.text_input("Endereço do Inquilino")
    rent_amount = st.number_input("Valor do Aluguel", min_value=0.0, step=0.01)
    deposit_amount = st.number_input("Valor do Depósito", min_value=0.0, step=0.01)

    # Botão para criar contrato
    if st.button("Criar Contrato"):
        contract_data = {
            "landlord": landlord,
            "tenant": tenant,
            "rent_amount": rent_amount,
            "deposit_amount": deposit_amount
        }

        response = requests.post(f"{DJANGO_API_URL}create/", json=contract_data)

        if response.status_code == 201:
            st.success("Contrato criado com sucesso!")
        else:
            st.error(f"Erro ao criar contrato: {response.status_code}")

if page == "Assinar Contrato":
    st.title("Assinar Contrato Inteligente")
    
    # Input para chave privada e ID do contrato
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")
    
    if st.button("Assinar Contrato"):
        # Lógica para assinar o contrato (via backend Django)
        signature_data = {
            "contract_id": contract_id,
            "private_key": private_key
        }
        response = requests.post(f"{DJANGO_API_URL}sign/", json=signature_data)
        
        if response.status_code == 200:
            st.success("Contrato assinado com sucesso!")
        else:
            st.error(f"Erro ao assinar contrato: {response.status_code}")

if page == "Executar Contrato":
    st.title("Executar Contrato Inteligente")
    
    contract_id = st.text_input("ID do Contrato")
    
    if st.button("Executar Contrato"):
        # Lógica para executar o contrato na blockchain
        execution_data = {
            "contract_id": contract_id
        }
        response = requests.post(f"{DJANGO_API_URL}execute/", json=execution_data)
        
        if response.status_code == 200:
            st.success("Contrato executado com sucesso!")
        else:
            st.error(f"Erro ao executar contrato: {response.status_code}")

if page == "Registrar Pagamento":
    st.title("Registrar Pagamento")
    
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")
    payment_type = st.selectbox("Tipo de Pagamento", ["Aluguel", "Depósito"])
    amount = st.number_input("Valor do Pagamento", min_value=0.0, step=0.01)
    
    if st.button("Registrar Pagamento"):
        # Lógica para registrar o pagamento
        payment_data = {
            "contract_id": contract_id,
            "private_key": private_key,
            "payment_type": payment_type,
            "amount": amount
        }
        response = requests.post(f"{DJANGO_API_URL}register_payment/", json=payment_data)
        
        if response.status_code == 200:
            st.success(f"Pagamento de {payment_type} registrado com sucesso!")
        else:
            st.error(f"Erro ao registrar pagamento: {response.status_code}")

if page == "Visualizar Contratos":
    st.title("Lista de Contratos de Aluguel")
    
    # Buscar contratos da API
    response = requests.get(f"{DJANGO_API_URL}contracts/")
    if response.status_code == 200:
        contracts = response.json()
        
        if contracts:
            for contract in contracts:
                st.subheader(f"Contrato de {contract['landlord']} para {contract['tenant']}")
                st.write(f"Valor do Aluguel: {contract['rent_amount']}")
                st.write(f"Valor do Depósito: {contract['deposit_amount']}")
                st.write(f"Endereço do Contrato na Blockchain: {contract['contract_address']}")
                st.markdown("---")
        else:
            st.write("Nenhum contrato encontrado.")
    else:
        st.error("Erro ao carregar contratos.")

if page == "Encerrar Contrato":
    st.title("Encerrar Contrato Inteligente")
    
    contract_id = st.text_input("ID do Contrato")
    private_key = st.text_input("Chave Privada", type="password")
    
    if st.button("Encerrar Contrato"):
        # Lógica para encerrar o contrato
        termination_data = {
            "contract_id": contract_id,
            "private_key": private_key
        }
        response = requests.post(f"{DJANGO_API_URL}terminate/", json=termination_data)
        
        if response.status_code == 200:
            st.success("Contrato encerrado com sucesso!")
        else:
            st.error(f"Erro ao encerrar contrato: {response.status_code}")
