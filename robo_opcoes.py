import sqlite3
from datetime import datetime
import pandas as pd

# 1. Dados de mercado simulados para BOVA11, PETR4 e VALE3
dados_mercado = {
    "Ativo": ["BOVA11", "PETR4", "VALE3"],
    "Preco_Spot": [120.00, 38.00, 62.00],
    "Premio_Put": [1.20, 0.70, 0.75]
}

df = pd.DataFrame(dados_mercado)

# 2. Parâmetros da Estratégia
margem_seguranca = 0.05       # 5% abaixo do preço atual (Strike OTM)
aliquota_ir = 0.15            # 15% de Imposto de Renda
capital_por_ativo = 10000.00  # R$ 10.000,00 por ativo
data_hoje = datetime.now().strftime("%Y-%m-%d")

# 3. Cálculos automáticos em lote usando o Pandas
df["Strike"] = df["Preco_Spot"] * (1 - margem_seguranca)
df["Quantidade"] = (capital_por_ativo / df["Strike"]).astype(int)
df["Valor_Investido"] = df["Quantidade"] * df["Strike"]  # Capital real alocado
df["Premio_Total"] = df["Premio_Put"] * df["Quantidade"]
df["Retorno_Mes"] = (df["Premio_Total"] / capital_por_ativo) * 100
df["Imposto"] = df["Premio_Total"] * aliquota_ir

print("=" * 80)
print("             RESULTADO DA SIMULAÇÃO (COM QUANTIDADE E VALOR)")
print("=" * 80)
print(df[["Ativo", "Preco_Spot", "Strike", "Quantidade", "Valor_Investido", "Premio_Total", "Retorno_Mes"]])
print("=" * 80)

# 4. Conectar e gravar os dados atualizados na base de dados SQLite
conexao = sqlite3.connect(r"C:\opcoes\opcoes.db")
cursor = conexao.cursor()

# Recriar a tabela para incluir as colunas de Quantidade e Valor Investido
cursor.execute("DROP TABLE IF EXISTS historico_simulacoes")

cursor.execute("""
    CREATE TABLE historico_simulacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_execucao TEXT,
        ativo TEXT,
        preco_spot REAL,
        strike REAL,
        quantidade INTEGER,
        valor_investido REAL,
        premio_total REAL,
        retorno_mes REAL,
        imposto REAL
    )
""")

# Inserir cada linha do Pandas na base de dados
for index, row in df.iterrows():
    cursor.execute("""
        INSERT INTO historico_simulacoes (
            data_execucao, ativo, preco_spot, strike, quantidade, valor_investido, premio_total, retorno_mes, imposto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_hoje, row["Ativo"], row["Preco_Spot"], row["Strike"], 
        int(row["Quantidade"]), row["Valor_Investido"], 
        row["Premio_Total"], row["Retorno_Mes"], row["Imposto"]
    ))

conexao.commit()
conexao.close()

print("\nSucesso! Tabela atualizada com Quantidade e Valor Investido em 'C:\\opcoes\\opcoes.db'.")
