#!/bin/bash

echo "Ativando o ambiente virtual..."
source venv/Scripts/activate

echo "Executando testes e gerando relatório de cobertura..."
coverage run manage.py test

if [ $? -eq 0 ]; then
    echo "Todos os testes passaram. Gerando relatório de cobertura em HTML..."

    coverage html

    echo "Abrindo o relatório de cobertura..."

    start htmlcov/index.html
else
    echo "Alguns testes falharam. Por favor, corrija os erros e tente novamente."
    exit 1
fi

echo "Compilando o contrato Solidity..."
python scripts/compilar_contrato.py

# Aplicar migrações, se necessário
echo "Aplicando migrações..."
python manage.py makemigrations
python manage.py migrate

# Iniciar o servidor Django
echo "Iniciando o servidor Django..."
python manage.py runserver 0.0.0.0:8000 &

# Iniciar o Streamlit
echo "Iniciando o Streamlit..."
streamlit run streamlit_app.py &

echo "Projeto iniciado com sucesso!"
