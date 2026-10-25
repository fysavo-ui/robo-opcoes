import streamlit as st
import sqlite3
import pandas as pd
from seguranca import check_password

# Interrompe a execução caso o utilizador não esteja autenticado
if not check_password():
    st.stop()

# ==========================================
# PAINEL PRINCIPAL (Apenas visível após login)
# ==========================================
st.title("Sistema de Opções - Painel de Controlo")
st.success("Acesso autorizado com sucesso!")

st.write("Bem-vindo ao seu painel modular de opções na nuvem.")

# Exemplo de botão para interagir com a base de dados
if st.button("Executar Varredura / Atualizar Dados"):
    st.info("A processar rotina de opções...")
    # Aqui pode chamar as funções dos seus módulos de backend (ex: database.py)
