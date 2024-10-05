#!/bin/bash

# Ativar o ambiente virtual
echo "Ativando o ambiente virtual..."
source venv/Scripts/activate



# Rodar os testes primeiro
# echo "Executando testes..."
# python manage.py test

# Verificar se os testes passaram
# if [ $? -eq 0 ]; then
    # echo "Todos os testes passaram. Iniciando o servidor..."

echo "Compilando o contrato Solidity..."
python scripts/compilar_contrato.py

# Aplicar migrações, se necessário
echo "Aplicando migrações..."
python manage.py makemigrations
python manage.py migrate

# Iniciar o servidor Django
echo "Iniciando o servidor Django..."
python manage.py runserver &

# Iniciar o Streamlit
echo "Iniciando o Streamlit..."
streamlit run streamlit_app.py &

echo "Projeto iniciado com sucesso!"
