@echo off
start cmd /k "npx hardhat node"
start cmd /k "venv\Scripts\activate && python manage.py runserver"
start cmd /k "venv\Scripts\activate && streamlit run streamlit_app.py"
