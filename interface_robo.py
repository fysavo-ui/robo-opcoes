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
            # Estabelece ligação à base de dados SQLite local
            conn = sqlite3.connect("opcoes.db")
            
            # Filtra para ignorar tabelas internas do SQLite e mostrar apenas as suas
            tabelas_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';", conn)
            
            if not tabelas_df.empty:
                lista_tabelas = tabelas_df['name'].tolist()
                
                # Cria um menu suspenso para escolher qual tabela visualizar
                tabela_escolhida = st.selectbox("Selecione a tabela que deseja consultar:", lista_tabelas)
                
                st.subheader(f"Registos da tabela: {tabela_escolhida}")
                
                # Lê e exibe os dados da tabela escolhida
                dados_df = pd.read_sql(f"SELECT * FROM {tabela_escolhida}", conn)
                if not dados_df.empty:
                    st.dataframe(dados_df)
                    st.caption(f"Total de registos encontrados: {len(dados_df)}")
                else:
                    st.warning("A tabela selecionada está atualmente vazia.")
            else:
                st.warning("A base de dados ainda não contém tabelas criadas.")
                
            conn.close()
            
        except Exception as e:
            st.error(f"Ocorreu um erro ao aceder à base de dados: {e}")
