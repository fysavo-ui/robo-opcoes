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

# Botão para efetuar a consulta à base de dados
if st.button("Consultar Dados / Atualizar"):
    with st.spinner("A consultar a base de dados..."):
        try:
            # Estabelece ligação à base de dados SQLite local do projeto
            conn = sqlite3.connect("opcoes.db")
            
            # Verifica que tabelas existem na base de dados
            tabelas_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            
            if not tabelas_df.empty:
                st.info("Tabelas encontradas na base de dados:")
                st.dataframe(tabelas_df)
                
                # Exemplo: Lê e exibe o conteúdo da primeira tabela disponível
                primeira_tabela = tabelas_df.iloc[0]['name']
                st.subheader(f"Registos da tabela: {primeira_tabela}")
                
                dados_df = pd.read_sql(f"SELECT * FROM {primeira_tabela}", conn)
                if not dados_df.empty:
                    st.dataframe(dados_df)
                else:
                    st.warning("A tabela selecionada está atualmente vazia.")
            else:
                st.warning("A base de dados ainda não contém tabelas criadas. Execute a rotina do robô primeiro para popular os dados.")
                
            conn.close()
            
        except Exception as e:
            st.error(f"Ocorreu um erro ao aceder à base de dados: {e}")
