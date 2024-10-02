import streamlit as st
import requests
import web3

# Defina o URL da API Django
DJANGO_API_URL = "http://localhost:8000/"

# Função para buscar contratos da API Django
def fetch_contracts():
    response = requests.get(f"{DJANGO_API_URL}api/contracts/")
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Menu de navegação para páginas diferentes
st.sidebar.title("Gestão de Contratos Inteligentes")
page = st.sidebar.selectbox("Selecione a página",
                        ["Criar Contrato",
                         "Assinar Contrato",
                         "Executar Contrato",
                         "Registrar Pagamento",
                         "Visualizar Contratos",
                         "Encerrar Contrato"])

if page == "Criar Contrato":
    st.title("Criar Novo Contrato")
    
    landlord = st.text_input("Endereço do Locador")
    tenant = st.text_input("Endereço do Inquilino")
    rent_amount = st.number_input("Valor do Aluguel", min_value=0.0, step=0.01)
    deposit_amount = st.number_input("Valor do Depósito", min_value=0.0, step=0.01)
    private_key = st.text_input("Chave Privada do Locador", type="password")

    # Botão para criar contrato
    if st.button("Criar Contrato"):
        contract_data = {
            "landlord": landlord,
            "tenant": tenant,
            "rent_amount": rent_amount,
            "deposit_amount": deposit_amount,
            "private_key": private_key
        }
        
        landlord = web3.Web3.to_checksum_address(landlord)
        tenant = web3.Web3.to_checksum_address(tenant)
        
        st.write("Enviando dados:", contract_data)

        response = requests.post(f"{DJANGO_API_URL}/api/create/", json=contract_data)

        if response.status_code == 201:
            st.success("Contrato criado com sucesso!")
        else:
            st.error(f"Erro ao criar contrato: {response.status_code} - {response.text}")

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
        response = requests.post(f"{DJANGO_API_URL}api/sign_contract/", json=signature_data)
        
        if response.status_code == 200:
            st.success("Contrato assinado com sucesso!")
        else:
            st.error(f"Erro ao assinar contrato: {response.status_code} - {response.text}")

if page == "Executar Contrato":
    st.title("Executar Contrato Inteligente")
    
    contract_id = st.text_input("ID do Contrato")
    
    if st.button("Executar Contrato"):
        # Lógica para executar o contrato na blockchain
        execution_data = {
            "contract_id": contract_id
        }
        response = requests.post(f"{DJANGO_API_URL}api/execute_contract/", json=execution_data)
        
        if response.status_code == 200:
            st.success("Contrato executado com sucesso!")
        else:
            st.error(f"Erro ao executar contrato: {response.status_code} - {response.text}")

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
        response = requests.post(f"{DJANGO_API_URL}api/register_payment/", json=payment_data)
        
        if response.status_code == 200:
            st.success(f"Pagamento de {payment_type} registrado com sucesso!")
        else:
            st.error(f"Erro ao registrar pagamento: {response.status_code} - {response.text}")

if page == "Visualizar Contratos":
    st.title("Lista de Contratos de Aluguel")
    
    # Buscar contratos da API
    response = requests.get(f"{DJANGO_API_URL}/api/contracts/")
    if response.status_code == 200:
        contracts = response.json()
        
        if contracts:
            for contract in contracts:
                st.subheader(f"Contrato de {contract['landlord']} para {contract['tenant']}")
                st.write(f"Valor do Aluguel: {contract['rent_amount']}")
                st.write(f"Valor do Depósito: {contract['deposit_amount']}")
                st.write(f"Endereço do Contrato na Blockchain: {contract['contract_address']}")
                st.write(f"Data de Criação: {contract['created_at']}")
                
                # Exibir pagamentos relacionados
                response_payments = requests.get(f"{DJANGO_API_URL}/api/payments/{contract['id']}/")
                if response_payments.status_code == 200:
                    payments = response_payments.json()
                    for payment in payments:
                        st.write(f"Pagamento: {payment['payment_type']} de {payment['amount']} em {payment['payment_date']}")
                
                # Verificar encerramento
                response_termination = requests.get(f"{DJANGO_API_URL}/api/termination/{contract['id']}/")
                if response_termination.status_code == 200:
                    termination = response_termination.json()
                    st.write(f"Contrato Encerrado em: {termination['termination_date']} por {termination['terminated_by']}")
                
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
        response = requests.post(f"{DJANGO_API_URL}api/terminate/", json=termination_data)
        
        if response.status_code == 200:
            st.success("Contrato encerrado com sucesso!")
        else:
            st.error(f"Erro ao encerrar contrato: {response.status_code} - {response.text}")
