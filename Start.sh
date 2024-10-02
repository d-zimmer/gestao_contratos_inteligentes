#!/bin/bash

# Ativar o ambiente virtual
echo "Ativando o ambiente virtual..."
source venv/Scripts/activate

# Certifique-se de que o Ganache GUI está em execução manualmente antes de iniciar o Django e o Streamlit
echo "Certifique-se de que o Ganache GUI está rodando..."

# Rodar os testes primeiro
# echo "Executando testes..."
# python manage.py test

# Verificar se os testes passaram
# if [ $? -eq 0 ]; then
    # echo "Todos os testes passaram. Iniciando o servidor..."


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
# else
    # echo "Alguns testes falharam. Corrija os erros antes de iniciar o servidor."
    # exit 1  # Interromper o script se os testes falharem
fi+
