#!/bin/bash

# Ativar o ambiente virtual
echo "Ativante o ambiente virtual..."
source venv/Scripts/activate

# Certifique-se de que o Ganache GUI está em execução manualmente antes de iniciar o Django e o Streamlit
echo "Certifique-se de que o Ganache GUI está rodando..."

# Iniciar o servidor Django
echo "Iniciando o servidor Django..."
python manage.py runserver &

# Iniciar o Streamlit
echo "Iniciando o Streamlit..."
streamlit run streamlit_app.py &

echo "Projeto iniciado com sucesso!"
