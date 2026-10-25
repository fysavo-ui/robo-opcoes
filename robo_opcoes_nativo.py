from datetime import datetime
import json
import sqlite3
import urllib.request
import pandas as pd

# ==========================================
# PAINEL DE PARAMETRIZAÇÃO E CONFIGURAÇÃO
# ==========================================
CONFIG = {
    "TICKER": "BOVA11.SA",
    "CAPITAL_DISPONIVEL": 15000.00,
    "MARGEM_SEGURANCA": 0.05,       # 5% OTM
    "META_RETORNO": 5.0,            # Meta de retorno mensal (%)
    "ALIQUOTA_IR": 0.15,            # 15% de IR
    "MIN_VOLUME": 500,              # Filtro de liquidez mínima
    "MODO_OPERACAO": "SIMULACAO"    # "SIMULACAO", "ALERTA", "SEMI_AUTO", "AUTONOMO"
}

data_hora_execucao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print(f"[{CONFIG['MODO_OPERACAO']}] A monitorizar {CONFIG['TICKER']} em {data_hora_execucao}...\n".replace(",", "X").replace(".", ",").replace("X", "."))

# Obter dados do Yahoo Finance
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{CONFIG['TICKER']}?interval=1d&range=1mo"

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        resultado_mercado = data['chart']['result'][0]
        preco_spot = resultado_mercado['meta']['regularMarketPrice']
        precos_historicos = [c for c in resultado_mercado['indicators']['quote'][0]['close'] if c is not None]
except Exception as e:
    print(f"Aviso: Não foi possível ligar à web ({e}). A usar preço de segurança.")
    preco_spot = 120.00
    precos_historicos = [120.00] * 20

# Calcular Média Móvel Simples (SMA 20)
sma_20 = sum(precos_historicos[-20:]) / 20 if len(precos_historicos) >= 20 else preco_spot

# Decisão automática de estratégia, Delta e Volume
if preco_spot < sma_20:
    estrategia = "VENDA_PUT"
    strike = preco_spot * (1 - CONFIG["MARGEM_SEGURANCA"])
    codigo_opcao = f"BOVA11W{int(strike)}"
    tipo_opcao = "PUT"
    premio_unitario = round(preco_spot * 0.042, 2)
    delta = -0.26
    volume_opcao = 1250
else:
    estrategia = "VENDA_CALL"
    strike = preco_spot * (1 + CONFIG["MARGEM_SEGURANCA"])
    codigo_opcao = f"BOVA11K{int(strike)}"
    tipo_opcao = "CALL"
    premio_unitario = round(preco_spot * 0.035, 2)
    delta = 0.24
    volume_opcao = 980

vencimento = "20/11/2026"

# Cálculos financeiros
quantidade = int(CONFIG["CAPITAL_DISPONIVEL"] / strike)
valor_investido = quantidade * strike
premio_total = premio_unitario * quantidade
retorno_mes = (premio_total / CONFIG["CAPITAL_DISPONIVEL"]) * 100
imposto = premio_total * CONFIG["ALIQUOTA_IR"]

# Avaliação da Meta e Liquidez
meta_atingida = retorno_mes >= CONFIG["META_RETORNO"]
liquidez_aprovada = volume_opcao >= CONFIG["MIN_VOLUME"]

if meta_atingida and liquidez_aprovada:
    status_negocio = "APROVADO (Meta e Liquidez OK)"
elif meta_atingida and not liquidez_aprovada:
    status_negocio = "REJEITADO (Baixa Liquidez / Volume)"
else:
    status_negocio = "AGUARDANDO META"

# ==========================================
# GESTÃO DA BASE DE DADOS (Migração Automática)
# ==========================================
conexao = sqlite3.connect("opcoes.db")
cursor = conexao.cursor()

# 1. Criar a tabela base caso não exista
cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_simulacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT,
        ativo TEXT,
        estrategia TEXT,
        tipo TEXT,
        codigo_opcao TEXT,
        vencimento TEXT,
        preco_spot REAL,
        strike REAL
    )
""")

# 2. Garantir que todas as colunas mais recentes existem no banco antigo
colunas_necessarias = [
    ("delta", "REAL"),
    ("volume", "INTEGER"),
    ("quantidade", "INTEGER"),
    ("valor_investido", "REAL"),
    ("premio_total", "REAL"),
    ("retorno_mes", "REAL"),
    ("status", "TEXT"),
    ("modo_operacao", "TEXT")
]

for coluna, tipo in colunas_necessarias:
    try:
        cursor.execute(f"ALTER TABLE historico_simulacoes ADD COLUMN {coluna} {tipo}")
    except sqlite3.OperationalError:
        pass  # A coluna já existe, passa à frente sem erro

# Inserir o novo registo com todos os campos preenchidos
cursor.execute("""
    INSERT INTO historico_simulacoes (
        data_hora, ativo, estrategia, tipo, codigo_opcao, vencimento, preco_spot, strike, 
        delta, volume, quantidade, valor_investido, premio_total, retorno_mes, status, modo_operacao
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    data_hora_execucao, "BOVA11", estrategia, tipo_opcao, codigo_opcao, 
    vencimento, preco_spot, strike, delta, volume_opcao, quantidade, 
    valor_investido, premio_total, retorno_mes, status_negocio, CONFIG["MODO_OPERACAO"]
))

conexao.commit()
conexao.close()

# Exibir tabela detalhada na consola
dados_exibicao = [{
    "data_hora": data_hora_execucao,
    "estrategia": estrategia,
    "tipo": tipo_opcao,
    "codigo_opcao": codigo_opcao,
    "delta": delta,
    "volume": volume_opcao,
    "retorno_mes": f"{retorno_mes:.2f}%".replace(".", ","),
    "status": status_negocio
}]
df = pd.DataFrame(dados_exibicao)

print("=" * 135)
print(f"   RELATÓRIO DE MONITORIZAÇÃO | Spot: R$ {preco_spot:.2f} | SMA20: R$ {sma_20:.2f}".replace(".", ","))
print("=" * 135)
print(df.to_string(index=False))
print("=" * 135)
print(f"\nSucesso! Registo guardado com o modo '{CONFIG['MODO_OPERACAO']}' e todos os parâmetros operacionais.")
