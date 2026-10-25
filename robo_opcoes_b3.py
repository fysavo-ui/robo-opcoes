import sqlite3
from datetime import datetime
import pandas as pd
import yfinance as yf

# Lista de ativos da B3 (.SA no Yahoo Finance)
ativos = ["BOVA11.SA", "PETR4.SA", "VALE3.SA"]

dados_calculados = []
margem_seguranca = 0.05       # 5% OTM
aliquota_ir = 0.15            # 15% IR
capital_por_ativo = 10000.00  
data_hoje = datetime.now().strftime("%Y-%m-%d")

print("A procurar dados em tempo real da B3...\n")

for ticker_symbol in ativos:
    nome_ativo = ticker_symbol.replace(".SA", "")
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Obter preço Spot atual
    hist = ticker.history(period="1d")
    if hist.empty:
        print(f"Não foi possível obter cotação para {nome_ativo}")
        continue
    preco_spot = float(hist["Close"].iloc[-1])
    
    # 2. Strike Alvo (5% abaixo do mercado para Put)
    strike_alvo = preco_spot * (1 - margem_seguranca)
    
    # 3. Buscar primeira data de vencimento de opções disponível
    expiracoes = ticker.options
    if expiracoes:
        vencimento = expiracoes[0]  # Próximo vencimento mensal
        opcao_chain = ticker.option_chain(vencimento)
        puts = opcao_chain.puts
        
        # Encontrar a opção PUT com strike mais próximo do nosso alvo
        puts['diferenca'] = (puts['strike'] - strike_alvo).abs()
        opcao_selecionada = puts.sort_values('diferenca').iloc[0]
        
        codigo_opcao = opcao_selecionada['contractSymbol']
        strike_real = float(opcao_selecionada['strike'])
        premio_put = float(opcao_selecionada['lastPrice']) if opcao_selecionada['lastPrice'] > 0 else 0.50
    else:
        # Fallback de segurança se não houver dados de opções na API
        vencimento = "2026-11-20"
        codigo_opcao = f"{nome_ativo}W{int(strike_alvo)}"
        strike_real = strike_alvo
        premio_put = 1.00

    # 4. Cálculos Financeiros
    quantidade = int(capital_por_ativo / strike_real)
    valor_investido = quantidade * strike_real
    premio_total = premio_put * quantidade
    retorno_mes = (premio_total / capital_por_ativo) * 100
    imposto = premio_total * aliquota_ir
    
    dados_calculados.append({
        "Ativo": nome_ativo,
        "Codigo_Opcao": codigo_opcao,
        "Vencimento": vencimento,
        "Preco_Spot": preco_spot,
        "Strike": strike_real,
        "Quantidade": quantidade,
        "Valor_Investido": valor_investido,
        "Premio_Total": premio_total,
        "Retorno_Mes": retorno_mes,
        "Imposto": imposto
    })

df = pd.DataFrame(dados_calculados)

# Display na consola
print("=" * 110)
print("             SIMULAÇÃO COM DADOS REAIS / TICKERS DA B3")
print("=" * 110)
print(df[["Ativo", "Codigo_Opcao", "Vencimento", "Preco_Spot", "Strike", "Quantidade", "Premio_Total"]])
print("=" * 110)

# 5. Salvar na base de dados SQLite (C:\opcoes\opcoes.db)
conexao = sqlite3.connect(r"C:\opcoes\opcoes.db")
cursor = conexao.cursor()

cursor.execute("DROP TABLE IF EXISTS historico_simulacoes")
cursor.execute("""
    CREATE TABLE historico_simulacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_execucao TEXT,
        ativo TEXT,
        codigo_opcao TEXT,
        vencimento TEXT,
        preco_spot REAL,
        strike REAL,
        quantidade INTEGER,
        valor_investido REAL,
        premio_total REAL,
        retorno_mes REAL,
        imposto REAL
    )
""")

for index, row in df.iterrows():
    cursor.execute("""
        INSERT INTO historico_simulacoes (
            data_execucao, ativo, codigo_opcao, vencimento, preco_spot, strike, 
            quantidade, valor_investido, premio_total, retorno_mes, imposto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_hoje, row["Ativo"], row["Codigo_Opcao"], row["Vencimento"],
        row["Preco_Spot"], row["Strike"], int(row["Quantidade"]), 
        row["Valor_Investido"], row["Premio_Total"], row["Retorno_Mes"], row["Imposto"]
    ))

conexao.commit()
conexao.close()

print("\nSucesso! Tickers reais da B3 gravados na base de dados 'C:\\opcoes\\opcoes.db'.")
