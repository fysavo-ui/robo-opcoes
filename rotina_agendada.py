from datetime import datetime
import json
import urllib.request
import database

def executar_rotina():
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] A iniciar rotina de opções...")
    
    # Obter os portfólios configurados e salvos no banco de dados
    fisicos = database.carregar_portfolio_fisico()
    livres = database.carregar_portfolio_livre()
    
    resultados_ciclo = []
    data_hora_execucao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    vencimento = "20/11/2026"
    
    min_volume = 300
    modo_operacao = "AUTONOMO"

    # ==========================================
    # 1. PROCESSAR CARTEIRA FÍSICA
    # ==========================================
    for ticker_fisica, qtd_total_acoes, meta_fisica in fisicos:
        if not ticker_fisica:
            continue
        nome_fisica = ticker_fisica.replace(".SA", "").upper()

        url_fisica = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_fisica}?interval=1d&range=1d"
        try:
            req = urllib.request.Request(url_fisica, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                preco_spot_f = data['chart']['result'][0]['meta']['regularMarketPrice']
        except Exception:
            preco_spot_f = 20.00

        strike_f = preco_spot_f * 1.05
        codigo_f = f"{nome_fisica}K{int(strike_f)}" if preco_spot_f > 20 else f"{nome_fisica}K{int(strike_f*100):02d}"
        premio_u_f = round(preco_spot_f * 0.03, 2)
        premio_tot_f = premio_u_f * qtd_total_acoes
        patrimonio_f = qtd_total_acoes * preco_spot_f
        ret_mes_f = (premio_tot_f / patrimonio_f) * 100 if patrimonio_f > 0 else 0.0
        vol_f = 1200

        status_f = "APROVADO (Meta OK)" if ret_mes_f >= meta_fisica and vol_f >= min_volume else "AGUARDANDO META"

        resultados_ciclo.append({
            "data_hora": data_hora_execucao, "ativo": nome_fisica, "estrategia": "CALL_COBERTA_FISICA",
            "tipo": "CALL", "codigo_opcao": codigo_f, "vencimento": vencimento, "preco_spot": preco_spot_f,
            "strike": strike_f, "delta": 0.25, "volume": vol_f, "quantidade": qtd_total_acoes,
            "valor_investido": patrimonio_f, "premio_total": premio_tot_f, "meta_objetivo": meta_fisica, "retorno_mes": ret_mes_f,
            "status": status_f, "modo_operacao": modo_operacao
        })

    # ==========================================
    # 2. PROCESSAR OPERAÇÃO LIVRE / CAIXA
    # ==========================================
    for ticker_livre, capital_livre, meta_livre in livres:
        if not ticker_livre:
            continue
        nome_livre = ticker_livre.replace(".SA", "").upper()

        url_livre = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_livre}?interval=1d&range=1mo"
        try:
            req = urllib.request.Request(url_livre, headers=headers)
            with urllib.request.urlopen(req) as response:
                data_l = json.loads(response.read().decode())
                res_l = data_l['chart']['result'][0]
                preco_spot_l = res_l['meta']['regularMarketPrice']
                precos_hist_l = [c for c in res_l['indicators']['quote'][0]['close'] if c is not None]
        except Exception:
            preco_spot_l = 100.00
            precos_hist_l = [100.00] * 20

        sma_20_l = sum(precos_hist_l[-20:]) / 20 if len(precos_hist_l) >= 20 else preco_spot_l

        if preco_spot_l < sma_20_l:
            estrategia_l = "VENDA_PUT"
            strike_l = preco_spot_l * 0.95
            codigo_l = f"{nome_livre}W{int(strike_l)}"
            tipo_l = "PUT"
            premio_u_l = round(preco_spot_l * 0.042, 2)
            delta_l = -0.26
            vol_l = 1500
        else:
            estrategia_l = "VENDA_CALL"
            strike_l = preco_spot_l * 1.05
            codigo_l = f"{nome_livre}K{int(strike_l)}"
            tipo_l = "CALL"
            premio_u_l = round(preco_spot_l * 0.035, 2)
            delta_l = 0.24
            vol_l = 980

        qtd_l = int(capital_livre / strike_l) if strike_l > 0 else 0
        val_inv_l = qtd_l * strike_l
        premio_tot_l = premio_u_l * qtd_l
        ret_mes_l = (premio_tot_l / capital_livre) * 100 if capital_livre > 0 else 0.0
        status_l = "APROVADO (Meta OK)" if ret_mes_l >= meta_livre and vol_l >= min_volume else "AGUARDANDO META"

        resultados_ciclo.append({
            "data_hora": data_hora_execucao, "ativo": nome_livre, "estrategia": estrategia_l,
            "tipo": tipo_l, "codigo_opcao": codigo_l, "vencimento": vencimento, "preco_spot": preco_spot_l,
            "strike": strike_l, "delta": delta_l, "volume": vol_l, "quantidade": qtd_l,
            "valor_investido": val_inv_l, "premio_total": premio_tot_l, "meta_objetivo": meta_livre, "retorno_mes": ret_mes_l,
            "status": status_l, "modo_operacao": modo_operacao
        })

    # ==========================================
    # 3. GRAVAR NO BANCO PARTILHADO (`opcoes.db`)
    # ==========================================
    if resultados_ciclo:
        database.gravar_resultados_e_inventario(resultados_ciclo, modo_operacao)
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Rotina concluída! {len(resultados_ciclo)} ativos analisados.")
    else:
        print("Aviso: Nenhum ativo configurado na base de dados para varredura.")

if __name__ == "__main__":
    executar_rotina()
