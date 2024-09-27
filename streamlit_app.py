import streamlit as st
import requests

# Defina o URL da API Django
DJANGO_API_URL_CONTRACTS = "http://localhost:8000/api/contracts/"
DJANGO_API_URL_CREATE = "http://localhost:8000/api/create/"

# Função para buscar contratos da API Django
def fetch_contracts():
    response = requests.get(DJANGO_API_URL_CONTRACTS)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Menu de navegação para páginas diferentes
st.sidebar.title("Navegação")
page = st.sidebar.radio("Ir para", ["Dashboard", "Criar Contrato"])

# Página de Dashboard (listagem de contratos)
if page == "Dashboard":
    st.title("Dashboard de Contratos de Aluguel")

    # Buscar contratos da API
    contracts = fetch_contracts()

    # Exibir contratos
    if contracts:
        for contract in contracts:
            st.subheader(f"Contrato de {contract['landlord']} para {contract['tenant']}")
            st.write(f"Valor do Aluguel: {contract['rent_amount']}")
            st.write(f"Valor do Depósito: {contract['deposit_amount']}")
            st.write(f"Endereço do Contrato na Blockchain: {contract['contract_address']}")
            st.markdown("---")
    else:
        st.write("Nenhum contrato encontrado.")

# Página para criar contratos
elif page == "Criar Contrato":
    st.title("Criar Novo Contrato")

    # Campos de entrada para o contrato
    landlord = st.text_input("Endereço do Locador")
    tenant = st.text_input("Endereço do Inquilino")
    rent_amount = st.number_input("Valor do Aluguel", min_value=0.0)
    deposit_amount = st.number_input("Valor do Depósito", min_value=0.0)

    # Botão para criar contrato
    if st.button("Criar Contrato"):
        if landlord and tenant and rent_amount > 0 and deposit_amount > 0:
            # Dados do contrato
            contract_data = {
                "landlord": landlord,
                "tenant": tenant,
                "rent_amount": rent_amount,
                "deposit_amount": deposit_amount
            }

            # Enviar a requisição POST para a API Django
            response = requests.post(DJANGO_API_URL_CREATE, json=contract_data)

            # Verificar a resposta da API
            if response.status_code == 201:
                st.success("Contrato criado com sucesso!")
            else:
                st.error(f"Erro ao criar contrato: {response.status_code}")
        else:
            st.warning("Preencha todos os campos corretamente.")
