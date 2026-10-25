import sqlite3
from datetime import datetime

def inicializar_banco():
    """Inicializa a base de dados, ativa o modo WAL e cria as tabelas necessárias."""
    conexao = sqlite3.connect("opcoes.db")
    conexao.execute("PRAGMA journal_mode=WAL;")
    cursor = conexao.cursor()
    
    # 1. Histórico de Simulações e Ordens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT, ativo TEXT, estrategia TEXT, tipo TEXT, codigo_opcao TEXT,
            vencimento TEXT, preco_spot REAL, strike REAL, delta REAL, volume INTEGER,
            quantidade INTEGER, valor_investido REAL, premio_total REAL, meta_objetivo REAL, retorno_mes REAL,
            status TEXT, modo_operacao TEXT
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE historico_simulacoes ADD COLUMN meta_objetivo REAL")
    except sqlite3.OperationalError:
        pass
    
    # 2. Portfólio Físico (Ações)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_fisico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            quantidade_total INTEGER,
            quantidade_coberta INTEGER,
            meta_retorno REAL
        )
    """)
    
    # 3. Portfólio Livre / Caixa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_livre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            capital_disponivel REAL,
            meta_retorno REAL
        )
    """)
    
    # 4. Tabela de Log de Inventário
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            tipo_evento TEXT,
            ticker TEXT,
            detalhes TEXT
        )
    """)
    
    conexao.commit()
    conexao.close()

def carregar_portfolio_fisico():
    conexao = sqlite3.connect("opcoes.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT ticker, quantidade_total, meta_retorno FROM portfolio_fisico")
    dados = cursor.fetchall()
    conexao.close()
    return dados

def carregar_portfolio_livre():
    conexao = sqlite3.connect("opcoes.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT ticker, capital_disponivel, meta_retorno FROM portfolio_livre")
    dados = cursor.fetchall()
    conexao.close()
    return dados

def registar_log(tipo_evento, ticker, detalhes, cursor_externo=None):
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if cursor_externo:
        cursor_externo.execute("""
            INSERT INTO log_inventario (data_hora, tipo_evento, ticker, detalhes)
            VALUES (?, ?, ?, ?)
        """, (data_hora, tipo_evento, ticker, detalhes))
    else:
        conexao = sqlite3.connect("opcoes.db")
        conexao.execute("PRAGMA journal_mode=WAL;")
        cursor = conexao.cursor()
        cursor.execute("""
            INSERT INTO log_inventario (data_hora, tipo_evento, ticker, detalhes)
            VALUES (?, ?, ?, ?)
        """, (data_hora, tipo_evento, ticker, detalhes))
        conexao.commit()
        conexao.close()

def sincronizar_portfolios_db(linhas_fisicas_dados, linhas_livres_dados):
    """Sincroniza a interface com a base de dados e audita alterações."""
    conexao = sqlite3.connect("opcoes.db")
    conexao.execute("PRAGMA journal_mode=WAL;")
    cursor = conexao.cursor()
    
    cursor.execute("SELECT ticker, quantidade_total, meta_retorno FROM portfolio_fisico")
    estado_anterior = {row[0]: {"qtd": row[1], "meta": row[2]} for row in cursor.fetchall()}
    
    estado_atual = {}
    for ticker, qtd, meta in linhas_fisicas_dados:
        ticker = ticker.strip().upper()
        if not ticker:
            continue
        try:
            estado_atual[ticker] = {"qtd": int(qtd), "meta": float(meta)}
        except ValueError:
            pass

    # 1. Exclusões
    for ticker_antigo in estado_anterior:
        if ticker_antigo not in estado_atual:
            antigo = estado_anterior[ticker_antigo]
            registar_log("EXCLUSÃO", ticker_antigo, f"Ativo removido (Tinha {antigo['qtd']} ações, Meta: {antigo['meta']}%).", cursor_externo=cursor)

    cursor.execute("DELETE FROM portfolio_fisico")

    # 2. Inclusões e Alterações
    for ticker, dados in estado_atual.items():
        qtd_atual = dados["qtd"]
        meta_atual = dados["meta"]
        
        if ticker not in estado_anterior:
            registar_log("INCLUSÃO", ticker, f"Novo ativo adicionado com {qtd_atual} ações | Meta definida: {meta_atual}%", cursor_externo=cursor)
        else:
            antigo = estado_anterior[ticker]
            mudancas = []
            if antigo["qtd"] != qtd_atual:
                diferenca = qtd_atual - antigo["qtd"]
                sinal = "+" if diferenca > 0 else ""
                mudancas.append(f"Qtd alterada de {antigo['qtd']} para {qtd_atual} ({sinal}{diferenca})")
            if antigo["meta"] != meta_atual:
                mudancas.append(f"Meta alterada de {antigo['meta']}% para {meta_atual}%")
            if mudancas:
                registar_log("ALTERAÇÃO", ticker, " | ".join(mudancas), cursor_externo=cursor)

        cursor.execute("""
            INSERT INTO portfolio_fisico (ticker, quantidade_total, quantidade_coberta, meta_retorno) 
            VALUES (?, ?, 0, ?)
        """, (ticker, qtd_atual, meta_atual))

    # Portfólio Livre
    cursor.execute("DELETE FROM portfolio_livre")
    for ticker, cap, meta in linhas_livres_dados:
        ticker = ticker.strip().upper()
        if not ticker:
            continue
        try:
            cursor.execute("INSERT INTO portfolio_livre (ticker, capital_disponivel, meta_retorno) VALUES (?, ?, ?)", (ticker, float(cap), float(meta)))
        except ValueError:
            pass
            
    conexao.commit()
    conexao.close()

def gravar_resultados_e_inventario(resultados_ciclo, modo_operacao):
    conexao = sqlite3.connect("opcoes.db")
    conexao.execute("PRAGMA journal_mode=WAL;")
    cursor = conexao.cursor()

    for r in resultados_ciclo:
        if "APROVADO" in r["status"] and modo_operacao in ["SEMI_AUTO", "AUTONOMO"] and r["estrategia"] == "CALL_COBERTA_FISICA":
            cursor.execute("UPDATE portfolio_fisico SET quantidade_coberta = quantidade_coberta + ? WHERE ticker = ?", (r["quantidade"], r["ativo"] + ".SA"))
            registar_log("LANÇAMENTO_ORDEM", r["ativo"] + ".SA", f"Ordem Call Coberta lançada para {r['quantidade']} ações (Meta: {r['meta_objetivo']}%).", cursor_externo=cursor)

        cursor.execute("""
            INSERT INTO historico_simulacoes (
                data_hora, ativo, estrategia, tipo, codigo_opcao, vencimento, preco_spot, strike, 
                delta, volume, quantidade, valor_investido, premio_total, meta_objetivo, retorno_mes, status, modo_operacao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["data_hora"], r["ativo"], r["estrategia"], r["tipo"], r["codigo_opcao"], 
            r["vencimento"], r["preco_spot"], r["strike"], r["delta"], r["volume"], 
            r["quantidade"], r["valor_investido"], r["premio_total"], r["meta_objetivo"], r["retorno_mes"], r["status"], r["modo_operacao"]
        ))
    
    conexao.commit()
    conexao.close()

def buscar_historico_db():
    conexao = sqlite3.connect("opcoes.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, data_hora, ativo, estrategia, tipo, codigo_opcao, preco_spot, strike, meta_objetivo, retorno_mes, status FROM historico_simulacoes ORDER BY id DESC")
    registos = cursor.fetchall()
    conexao.close()
    return registos

def buscar_logs_db():
    conexao = sqlite3.connect("opcoes.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, data_hora, tipo_evento, ticker, detalhes FROM log_inventario ORDER BY id DESC")
    registos = cursor.fetchall()
    conexao.close()
    return registos
