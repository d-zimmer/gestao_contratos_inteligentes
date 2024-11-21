import streamlit as st # type:ignore
import requests # type:ignore
import random
import os
import base64
from datetime import datetime, date, timedelta
from dotenv import load_dotenv # type:ignore
from web3 import Web3 # type:ignore
from scripts.gerar_pdf_contrato import gerar_pdf_contrato
from pytz import timezone # type:ignore

st.set_page_config(
    page_title="Gestão de Contratos",
    layout="centered",
    page_icon="scripts/flaticon.png"
)

load_dotenv()

DJANGO_API_URL = "http://gestaocontratos.brazilsouth.cloudapp.azure.com/"

brazil_tz = timezone("America/Sao_Paulo")

if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
    
def obter_endereco_locador():
    # Faz uma requisição para obter o endereço do locador
    response, success = api_get("api/get_landlord_address/")
    if success and "wallet_address" in response:
        return response["wallet_address"]
    else:
        st.error("Erro ao obter o endereço do locador.")
        return None

def get_address_from_private_key(private_key):
    account = Web3().eth.account.from_key(private_key)
    return account.address

def fetch_contract_events(contract_id):
    data, success = api_get(f"api/contracts/{contract_id}/events/")
    if success:
        return data
    else:
        return []

def download_link_pdf(pdf_content, filename="contrato.pdf"):
    b64 = base64.b64encode(pdf_content).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Baixar Contrato</a>'

def handle_logout():
    st.session_state["is_logged_in"] = False
    st.session_state["current_page"] = "login"

if st.session_state.get("is_logged_in", False):
    st.sidebar.button("Logout", on_click=handle_logout)

def preencher_contrato_automaticamente():
    landlord = obter_endereco_locador()  # Usa o endereço específico do locador
    tenant = st.session_state.get("user_address", "")
    rent_amount = random.randint(250, 1500)
    deposit_amount = random.randint(250, 1500)
    start_date = datetime.now()
    end_date = start_date + timedelta(minutes=2)
    contract_duration = 2
    return landlord, tenant, rent_amount, deposit_amount, start_date, end_date, contract_duration

def show_login_page():
    st.title("Login")
    login = st.text_input("Login", key="unique_login_key")

    if st.button("Entrar"):
        if not login:
            st.error("Login é obrigatório.")
        else:
            login_data = {"login": login}
            response, success = api_post("api/login/", login_data)

            if success:
                st.success("Login realizado com sucesso!")

                if "user_login" in response and "wallet_address" in response:
                    st.session_state["user_id"] = response["user_id"]
                    st.session_state["user_login"] = response["user_login"]
                    st.session_state["user_address"] = response["wallet_address"]
                    st.session_state["is_landlord"] = response.get("is_landlord", False)  # Adiciona o is_landlord aqui
                    st.session_state["is_logged_in"] = True
                    st.session_state["current_page"] = "home"
                    st.rerun()
                else:
                    st.error("Erro: 'user_login' ou 'wallet_address' não encontrado na resposta.")
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
    st.sidebar.title("Gestão de Contratos Inteligentes")
    page = st.sidebar.selectbox("Selecione a página",
                                ["Criar Contrato",
                                 "Assinar Contrato",
                                 "Registrar Pagamento",
                                 "Visualizar Contratos",
                                 "Encerrar Contrato"])
    
    brazil_tz = timezone("America/Sao_Paulo")

    if page == "Criar Contrato":
        st.title("Criar Novo Contrato")

        if not st.session_state.get("is_landlord", False):
            if st.button("Contrato Pendente"):
                landlord, tenant, rent_amount, deposit_amount, start_date, end_date, contract_duration = preencher_contrato_automaticamente()
                st.session_state["landlord"] = landlord
                st.session_state["tenant"] = tenant
                st.session_state["rent_amount"] = rent_amount
                st.session_state["deposit_amount"] = deposit_amount
                st.session_state["start_date"] = start_date
                st.session_state["end_date"] = end_date
                st.session_state["contract_duration"] = contract_duration

        landlord = st.text_input("Endereço do Locador", st.session_state.get("landlord", ""))
        tenant = st.text_input("Endereço do Inquilino", st.session_state.get("tenant", ""))
        rent_amount = st.number_input("Valor do Aluguel (Wei)", min_value=0, step=1, value=st.session_state.get("rent_amount", 0))
        deposit_amount = st.number_input("Valor do Depósito (Wei)", min_value=0, step=1, value=st.session_state.get("deposit_amount", 0))

        start_date_date = st.date_input("Data de Início do Contrato (Data)", st.session_state.get("start_date_date", datetime.now(brazil_tz).date()))
        start_date_time = st.time_input("Data de Início do Contrato (Hora)", st.session_state.get("start_date_time", datetime.now(brazil_tz).time()))
        start_date = brazil_tz.localize(datetime.combine(start_date_date, start_date_time))

        end_date_date = st.date_input("Data de Término do Contrato (Data)", st.session_state.get("end_date_date", (datetime.now(brazil_tz) + timedelta(minutes=2)).date()))
        end_date_time = st.time_input("Data de Término do Contrato (Hora)", st.session_state.get("end_date_time", (datetime.now(brazil_tz) + timedelta(minutes=2)).time()))
        end_date = brazil_tz.localize(datetime.combine(end_date_date, end_date_time))
        
        start_date_timestamp = int(start_date.timestamp())
        end_date_timestamp = int(end_date.timestamp())
        
        start_date_str = start_date.isoformat()  # Gera o "T" automaticamente
        end_date_str = end_date.isoformat()

        contract_duration = (end_date - start_date).total_seconds() // 60

        st.write(f"Duração do Contrato: {contract_duration} minutos")

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
                    "start_date": start_date_timestamp,
                    "end_date": end_date_timestamp,  
                    "contract_duration": contract_duration,  # Passando duração em minutos
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
                start_date_iso = contract['start_date'].split('+')[0]
                end_date_iso = contract['end_date'].split('+')[0]
                
                start_date = datetime.strptime(start_date_iso, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
                end_date = datetime.strptime(end_date_iso, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
                created_at = datetime.fromisoformat(contract['created_at'].replace('Z', '')).strftime('%d/%m/%Y %H:%M:%S')
                
                st.markdown(f"""
                ***Contrato {contract['id']}***
                - **Locador**: {contract['landlord']}  
                - **Inquilino**: {contract['tenant']}  
                - **Valor do Aluguel**: {contract['rent_amount']} ETH  
                - **Valor do Depósito**: {contract['deposit_amount']} ETH  
                - **Endereço do Contrato**: {contract['contract_address']}  
                - **Status**: {contract['status']}  
                - **Data de Início**: {start_date}
                - **Data de Término**: {end_date}  
                - **Data de Criação**: {created_at}
                """)
                
                events = fetch_contract_events(contract['id'])
                st.subheader("Eventos do Contrato")
                
                if events:
                    for event in events:
                        st.markdown(f"- **Tipo de Evento**: {event['event_type']}")
                        st.markdown(f"  - **Hash da Transação**: {event['tx_hash']}")
                        st.markdown(f"  - **Endereço do Usuário**: {event['from_address']}")
                        st.markdown(f"  - **Dados do Evento**: {event['event_data']}")
                        st.markdown(f"  - **Timestamp**: {event['timestamp']}")
                        st.markdown(f"  - **Bloco**: {event['block_number']}")
                        st.markdown(f"  - **Gas Usado**: {event['gas_used']}")
                        st.markdown("---")

                pdf_content = gerar_pdf_contrato(contract)
                st.download_button(
                    label="Clique para baixar o PDF",
                    data=pdf_content,
                    file_name=f"contrato_{contract['id']}.pdf",
                    mime="application/pdf",
                    key=f"download_{contract['id']}"
                )
                st.markdown("---")
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

# if st.session_state.get("current_page") != "login":
#     st.sidebar.button("Logout", on_click=handle_logout)