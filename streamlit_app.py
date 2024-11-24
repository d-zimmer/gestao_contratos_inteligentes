import streamlit as st # type:ignore
import requests # type:ignore
import random
import pandas as pd
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

DJANGO_API_URL = "https://gestaocontratos.brazilsouth.cloudapp.azure.com"

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

def fetch_contracts():
    data, success = api_get("api/contracts/")
    if success:
        return data
    else:
        return []
    
def fetch_users():
    response, success = api_get("api/get_users/")
    if success:
        return [user["wallet_address"] for user in response]
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
    start_date = datetime.now(brazil_tz)
    end_date = start_date + timedelta(minutes=2)
    contract_duration = 2
    return landlord, tenant, rent_amount, deposit_amount, start_date, end_date, contract_duration

def show_visualizar_contratos_page():
    st.title("Lista de Contratos de Aluguel")
    contracts = fetch_contracts()

    if contracts:
        # Exibir tabela inicial com IDs, Locador e Inquilino
        df = pd.DataFrame(contracts)
        selected_contract_id = st.selectbox(
            "Selecione um contrato para visualizar detalhes",
            df["id"],
            format_func=lambda x: f"Contrato {x}"
        )

        # Filtrar contrato selecionado
        selected_contract = next(
            (contract for contract in contracts if contract["id"] == selected_contract_id), None
        )

        if selected_contract:
            # Exibir detalhes do contrato selecionado
            with st.expander(f"Contrato {selected_contract['id']}", expanded=True):
                st.markdown(f"""
                **Locador:** {selected_contract['landlord']}  
                **Inquilino:** {selected_contract['tenant']}  
                **Valor do Aluguel:** {selected_contract['rent_amount']} ETH  
                **Valor do Depósito:** {selected_contract['deposit_amount']} ETH  
                **Endereço do Contrato:** {selected_contract['contract_address']}  
                **Status:** {selected_contract['status']}  
                **Data de Início:** {selected_contract['start_date']}  
                **Data de Término:** {selected_contract['end_date']}  
                **Data de Criação:** {selected_contract['created_at']}  
                """)
                # start_timestamp = int(datetime.combine(start_date, start_time).timestamp())
                # end_timestamp = int(datetime.combine(end_date, end_time).timestamp())

                # Buscar eventos relacionados ao contrato
                events = fetch_contract_events(selected_contract["id"])

                # Mostrar eventos diretamente, sem aninhar expanders
                st.subheader("Eventos do Contrato")
                if events:
                    for event in events:
                        st.markdown(f"""
                        - **Tipo de Evento:** {event['event_type']}  
                        - **Hash da Transação:** {event['tx_hash']}  
                        - **Endereço do Usuário:** {event['from_address']}  
                        - **Dados do Evento:** {event['event_data']}  
                        - **Timestamp:** {event['timestamp']}  
                        - **Bloco:** {event['block_number']}  
                        - **Gas Usado:** {event['gas_used']}  
                        """)
                        st.markdown("---")
                else:
                    st.info("Nenhum evento encontrado para este contrato.")

                # Botão para baixar PDF
                pdf_content = gerar_pdf_contrato(selected_contract)
                st.download_button(
                    label="Baixar PDF do Contrato",
                    data=pdf_content,
                    file_name=f"contrato_{selected_contract['id']}.pdf",
                    mime="application/pdf",
                )
    else:
        st.info("Nenhum contrato encontrado.")

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
                
def buscar_contrato_pendente():
    user_address = st.session_state.get("user_address", None)
    is_landlord = st.session_state.get("is_landlord", False)

    if not user_address:
        st.error("Endereço do usuário não encontrado.")
        return None

    # Determina o tipo de busca baseado no tipo de usuário
    endpoint = f"api/contracts/?{'landlord' if is_landlord else 'tenant'}={user_address}&status=pending"
    
    response, success = api_get(endpoint)

    if success and response:
        return response[0]  # Supondo que retorna o contrato pendente mais recente
    else:
        st.error("Nenhum contrato pendente encontrado.")
        return None

def preencher_contrato_com_pendente():
    """Preenche os campos do contrato com informações do contrato pendente."""
    contrato_pendente = buscar_contrato_pendente()
    if contrato_pendente:
        st.session_state["contract_id"] = contrato_pendente["id"]
        st.session_state["landlord"] = contrato_pendente["landlord"]
        st.session_state["tenant"] = contrato_pendente["tenant"]
        st.session_state["rent_amount"] = contrato_pendente["rent_amount"]
        st.session_state["deposit_amount"] = contrato_pendente["deposit_amount"]
        st.session_state["start_date"] = contrato_pendente["start_date"]
        st.session_state["end_date"] = contrato_pendente["end_date"]

def fetch_pending_contracts():
    user_type = "landlord" if st.session_state.get("is_landlord", False) else "tenant"
    user_address = st.session_state.get("user_address", "")
    response, success = api_get(f"api/pending_contracts/?user_address={user_address}&user_type={user_type}")
    if success:
        return response
    else:
        return []

def api_post(endpoint, data):
    try:
        response = requests.post(f"{DJANGO_API_URL}/{endpoint}", json=data)
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

    if page == "Criar Contrato":
        st.title("Criar ou Assinar Contrato")

        # Verifica se o usuário é Admin ou Inquilino
        if st.session_state.get("is_landlord", False):  # Caso seja Admin
            st.subheader("Criar Novo Contrato")
            
            # Botão para preenchimento automático
            if st.button("Preencher com Dados Padrão"):
                st.session_state["tenant"] = "0x1234567890abcdef1234567890abcdef12345678"  # Exemplo
                st.session_state["rent_amount"] = random.randint(250, 1500)
                st.session_state["deposit_amount"] = random.randint(100, 1000)
                st.session_state["start_date"] = datetime.now(brazil_tz).date()
                st.session_state["start_time"] = datetime.now(brazil_tz).time()
                st.session_state["end_date"] = (datetime.now(brazil_tz) + timedelta(minutes=2)).date()
                st.session_state["end_time"] = (datetime.now(brazil_tz) + timedelta(minutes=2)).time()
            
            # Campos para criar o contrato
            landlord = st.text_input("Endereço do Locador", st.session_state.get("user_address", ""))

            # Busca a lista de usuários para seleção do inquilino
            user_list = fetch_users()
            if user_list:
                tenant = st.selectbox("Selecione o Inquilino", options=[""] + user_list, key="tenant_select")
            else:
                tenant = st.text_input("Endereço do Inquilino", st.session_state.get("tenant", ""))
                st.warning("Nenhum usuário disponível para seleção. Insira manualmente.")

            rent_amount = st.number_input(
                "Valor do Aluguel (Wei)", 
                min_value=0.0,
                step=1.0,
                value=float(st.session_state.get("rent_amount", 0))  # Convertendo para float
            )
            deposit_amount = st.number_input(
                "Valor do Depósito (Wei)", 
                min_value=0.0,
                step=1.0,
                value=float(st.session_state.get("deposit_amount", 0))  # Convertendo para float
            )
            start_date = st.date_input("Data de Início do Contrato", value=st.session_state.get("start_date", datetime.now(brazil_tz).date()))
            start_time = st.time_input("Hora de Início do Contrato", value=st.session_state.get("start_time", datetime.now(brazil_tz).time()))
            end_date = st.date_input("Data de Término do Contrato", value=st.session_state.get("end_date", (datetime.now(brazil_tz) + timedelta(minutes=2)).date()))
            end_time = st.time_input("Hora de Término do Contrato", value=st.session_state.get("end_time", (datetime.now(brazil_tz) + timedelta(minutes=2)).time()))
            private_key = st.text_input("Chave Privada (Locador)", type="password")

            # Converte datas para timestamps
            start_timestamp = int(datetime.combine(start_date, start_time).timestamp())
            end_timestamp = int(datetime.combine(end_date, end_time).timestamp())
            contract_duration = (end_timestamp - start_timestamp) // 60

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
                        "start_date": start_timestamp,
                        "end_date": end_timestamp,
                        "private_key": private_key,
                    }
                    response, success = api_post("api/create/", contract_data)
                    if success:
                        st.success(f"Contrato criado com sucesso! Endereço do Contrato: {response['contract_address']}")
                    else:
                        st.error(f"Erro ao criar contrato: {response}")

    elif page == "Assinar Contrato":
        st.title("Assinar Contratos Pendentes")

        contracts = fetch_pending_contracts()

        if contracts:
            st.write(f"**Total de Contratos Pendentes:** {len(contracts)}")
            contract_options = {f"Contrato {contract['id']}": contract for contract in contracts}
            selected_contract = st.selectbox(
                "Selecione um contrato para assinar", list(contract_options.keys())
            )

            if selected_contract:
                contract = contract_options[selected_contract]
                st.subheader("Detalhes do Contrato Selecionado")
                st.write(f"**Locador:** {contract['landlord']}")
                st.write(f"**Inquilino:** {contract['tenant']}")
                st.write(f"**Valor do Aluguel:** {contract['rent_amount']} WEI")
                st.write(f"**Valor do Depósito:** {contract['deposit_amount']} WEI")
                st.write(f"**Status:** {contract['status']}")

                private_key = st.text_input(
                    "Insira sua Chave Privada para Assinar", type="password"
                )
                if st.button("Assinar Contrato"):
                    user_type = "landlord" if st.session_state.get("is_landlord", False) else "tenant"
                    if not private_key:
                        st.error("Chave privada é obrigatória para assinar.")
                    else:
                        response, success = api_post(
                            f"api/contracts/{contract['id']}/sign/",
                            {"private_key": private_key, "user_type": user_type},
                        )
                        if success:
                            st.success("Contrato assinado com sucesso!")
                        else:
                            st.error(f"Erro ao assinar contrato: {response}")
        else:
            st.info("Nenhum contrato pendente encontrado.")

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
        show_visualizar_contratos_page()

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