import tkinter as tk
from tkinter import messagebox, ttk

# Importar o banco e a rotina centralizada
import database
import rotina_agendada

# Listas globais para gerir as linhas dinâmicas na interface
linhas_fisicas = []
linhas_livres = []

def carregar_dados_salvos():
    fisicos = database.carregar_portfolio_fisico()
    for ticker, qtd, meta in fisicos:
        adicionar_linha_fisica(ticker, str(qtd), str(meta))
        
    livres = database.carregar_portfolio_livre()
    for ticker, cap, meta in livres:
        adicionar_linha_livre(ticker, str(cap), str(meta))

def sincronizar_banco_portfolio():
    dados_fisicos = [(e_ticker.get(), e_qtd.get(), e_meta.get()) for e_ticker, e_qtd, e_meta, _ in linhas_fisicas]
    dados_livres = [(e_ticker.get(), e_cap.get(), e_meta.get()) for e_ticker, e_cap, e_meta, _ in linhas_livres]
    database.sincronizar_portfolios_db(dados_fisicos, dados_livres)

# ==========================================
# FUNÇÕES DA INTERFACE GRÁFICA
# ==========================================
def adicionar_linha_fisica(ticker="", qtd="", meta=""):
    row_frame = tk.Frame(container_fisica, bg="#f0f0f0")
    row_frame.pack(fill="x", pady=2)
    
    tk.Label(row_frame, text="Ticker:", bg="#f0f0f0", width=6).pack(side="left")
    e_ticker = tk.Entry(row_frame, width=10)
    e_ticker.insert(0, ticker)
    e_ticker.pack(side="left", padx=2)
    
    tk.Label(row_frame, text="Qtd Total:", bg="#f0f0f0", width=7).pack(side="left")
    e_qtd = tk.Entry(row_frame, width=6)
    e_qtd.insert(0, qtd)
    e_qtd.pack(side="left", padx=2)
    
    tk.Label(row_frame, text="Meta(%):", bg="#f0f0f0", width=7).pack(side="left")
    e_meta = tk.Entry(row_frame, width=5)
    e_meta.insert(0, meta)
    e_meta.pack(side="left", padx=2)
    
    def remover():
        row_frame.destroy()
        linhas_fisicas.remove((e_ticker, e_qtd, e_meta, row_frame))
        sincronizar_banco_portfolio()
        
    btn_remover = tk.Button(row_frame, text="❌", bg="#ffcccc", fg="red", command=remover, width=3, relief="flat")
    btn_remover.pack(side="left", padx=5)
    
    linhas_fisicas.append((e_ticker, e_qtd, e_meta, row_frame))

def adicionar_linha_livre(ticker="", capital="", meta=""):
    row_frame = tk.Frame(container_livre, bg="#f0f0f0")
    row_frame.pack(fill="x", pady=2)
    
    tk.Label(row_frame, text="Ticker:", bg="#f0f0f0", width=6).pack(side="left")
    e_ticker = tk.Entry(row_frame, width=10)
    e_ticker.insert(0, ticker)
    e_ticker.pack(side="left", padx=2)
    
    tk.Label(row_frame, text="Capital(R$):", bg="#f0f0f0", width=9).pack(side="left")
    e_cap = tk.Entry(row_frame, width=10)
    e_cap.insert(0, capital)
    e_cap.pack(side="left", padx=2)
    
    tk.Label(row_frame, text="Meta(%):", bg="#f0f0f0", width=7).pack(side="left")
    e_meta = tk.Entry(row_frame, width=5)
    e_meta.insert(0, meta)
    e_meta.pack(side="left", padx=2)
    
    def remover():
        row_frame.destroy()
        linhas_livres.remove((e_ticker, e_cap, e_meta, row_frame))
        sincronizar_banco_portfolio()
        
    btn_remover = tk.Button(row_frame, text="❌", bg="#ffcccc", fg="red", command=remover, width=3, relief="flat")
    btn_remover.pack(side="left", padx=5)
    
    linhas_livres.append((e_ticker, e_cap, e_meta, row_frame))

def executar_varredura():
    try:
        sincronizar_banco_portfolio()
        rotina_agendada.executar_rotina()
    except ValueError:
        messagebox.showerror("Erro de Formato", "Por favor, verifique se os números, quantidades e metas estão corretos.")

def abrir_janela_historico():
    janela_hist = tk.Toplevel(root)
    janela_hist.title("Histórico de Simulações e Ordens")
    janela_hist.geometry("1050x450")
    
    tk.Label(janela_hist, text="Registos de Simulações Guardados", font=("Arial", 12, "bold")).pack(pady=10)
    
    frame_tabela = tk.Frame(janela_hist)
    frame_tabela.pack(fill="both", expand=True, padx=10, pady=5)
    
    colunas = ("ID", "Data/Hora", "Ativo", "Estratégia", "Tipo", "Opção", "Spot (R$)", "Strike (R$)", "Meta (%)", "Retorno (%)", "Status")
    tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=15)
    
    larguras = [40, 130, 70, 130, 50, 95, 80, 80, 75, 80, 160]
    for col, largura in zip(colunas, larguras):
        tree.heading(col, text=col)
        tree.column(col, width=largura, anchor="center")
        
    scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
    scrollbar_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar_y.pack(side="right", fill="y")
    
    try:
        registos = database.buscar_historico_db()
        for reg in registos:
            reg_formatado = list(reg)
            reg_formatado[6] = f"R$ {reg[6]:.2f}".replace(".", ",")
            reg_formatado[7] = f"R$ {reg[7]:.2f}".replace(".", ",")
            meta_val = reg[8] if reg[8] is not None else 0.0
            reg_formatado[8] = f"{meta_val:.2f}%".replace(".", ",")
            reg_formatado[9] = f"{reg[9]:.2f}%".replace(".", ",")
            tree.insert("", "end", values=reg_formatado)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler histórico: {e}")

def abrir_janela_log():
    janela_log = tk.Toplevel(root)
    janela_log.title("Log de Auditoria de Inventário")
    janela_log.geometry("850x420")
    
    tk.Label(janela_log, text="Registo de Inclusões, Exclusões e Alterações de Ações", font=("Arial", 12, "bold")).pack(pady=10)
    
    frame_tabela = tk.Frame(janela_log)
    frame_tabela.pack(fill="both", expand=True, padx=10, pady=5)
    
    colunas = ("ID", "Data/Hora", "Evento", "Ativo", "Detalhes da Alteração")
    tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=15)
    
    larguras = [40, 130, 100, 80, 470]
    for col, largura in zip(colunas, larguras):
        tree.heading(col, text=col)
        tree.column(col, width=largura, anchor="center" if col != "Detalhes da Alteração" else "w")
        
    scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_y.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar_y.pack(side="right", fill="y")
    
    try:
        registos = database.buscar_logs_db()
        for reg in registos:
            tree.insert("", "end", values=reg)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler log: {e}")

# ==========================================
# CONSTRUÇÃO DA TELA PRINCIPAL (TKINTER)
# ==========================================
database.inicializar_banco()

root = tk.Tk()
root.title("Painel de Controlo - Robô de Opções Parametrizado")
root.geometry("640x750")
root.config(bg="#f0f0f0")

lbl_titulo = tk.Label(root, text="Painel Multiativo com Auditoria de Inventário", font=("Arial", 13, "bold"), bg="#f0f0f0", fg="#333")
lbl_titulo.pack(pady=10)

# --- Frame Carteira Física ---
frame_fisica_outer = tk.LabelFrame(root, text=" 1. Carteira Física (Call Coberta - Inventário) ", font=("Arial", 10, "bold"), bg="#f0f0f0", padx=10, pady=5)
frame_fisica_outer.pack(fill="x", padx=15, pady=5)

container_fisica = tk.Frame(frame_fisica_outer, bg="#f0f0f0")
container_fisica.pack(fill="x", pady=2)

btn_add_fisica = tk.Button(frame_fisica_outer, text="➕ Adicionar Ação na Carteira", bg="#2196F3", fg="white", font=("Arial", 9, "bold"), command=lambda: adicionar_linha_fisica())
btn_add_fisica.pack(pady=5, anchor="w")

# --- Frame Operação Livre ---
frame_livre_outer = tk.LabelFrame(root, text=" 2. Operação Livre / Caixa (Múltiplos Ativos) ", font=("Arial", 10, "bold"), bg="#f0f0f0", padx=10, pady=5)
frame_livre_outer.pack(fill="x", padx=15, pady=5)

container_livre = tk.Frame(frame_livre_outer, bg="#f0f0f0")
container_livre.pack(fill="x", pady=2)

btn_add_livre = tk.Button(frame_livre_outer, text="➕ Adicionar Ativo Livre / Caixa", bg="#FF9800", fg="white", font=("Arial", 9, "bold"), command=lambda: adicionar_linha_livre())
btn_add_livre.pack(pady=5, anchor="w")

# --- Frame Configurações Gerais ---
frame_geral = tk.LabelFrame(root, text=" Configurações Gerais ", font=("Arial", 10, "bold"), bg="#f0f0f0", padx=10, pady=5)
frame_geral.pack(fill="x", padx=15, pady=5)

tk.Label(frame_geral, text="Volume Mínimo:", bg="#f0f0f0").grid(row=0, column=0, sticky="w", pady=2)
entry_min_volume = tk.Entry(frame_geral, width=15)
entry_min_volume.insert(0, "300")
entry_min_volume.grid(row=0, column=1, pady=2, padx=5)

tk.Label(frame_geral, text="Modo de Operação:", bg="#f0f0f0").grid(row=1, column=0, sticky="w", pady=2)
combo_modo = ttk.Combobox(frame_geral, values=["SIMULACAO", "ALERTA", "SEMI_AUTO", "AUTONOMO"], width=13, state="readonly")
combo_modo.set("SIMULACAO")
combo_modo.grid(row=1, column=1, pady=2, padx=5)

# --- Frame de Botões de Ação ---
frame_botoes = tk.Frame(root, bg="#f0f0f0")
frame_botoes.pack(pady=12)

btn_executar = tk.Button(
    frame_botoes, 
    text=" 🚀 Executar Varredura ", 
    font=("Arial", 9, "bold"), 
    bg="#4CAF50", 
    fg="white", 
    padx=8, 
    pady=5, 
    command=executar_varredura
)
btn_executar.pack(side="left", padx=3)

btn_listar = tk.Button(
    frame_botoes, 
    text=" 📊 Histórico Opções ", 
    font=("Arial", 9, "bold"), 
    bg="#607D8B", 
    fg="white", 
    padx=8, 
    pady=5, 
    command=abrir_janela_historico
)
btn_listar.pack(side="left", padx=3)

btn_log = tk.Button(
    frame_botoes, 
    text=" 📋 Log de Inventário ", 
    font=("Arial", 9, "bold"), 
    bg="#3F51B5", 
    fg="white", 
    padx=8, 
    pady=5, 
    command=abrir_janela_log
)
btn_log.pack(side="left", padx=3)

# Carregar dados gravados no banco ao iniciar
carregar_dados_salvos()

root.mainloop()
