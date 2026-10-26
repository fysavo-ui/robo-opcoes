import os

# Definição das pastas a criar
pastas = [
    ".streamlit",
    "sql",
    "modulos"
]

# Definição dos ficheiros iniciais e respetivo conteúdo base
ficheiros = {
    "requirements.txt": "streamlit\npandas\n",
    
    ".streamlit/config.toml": """[theme]
primaryColor = "#00A86B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
""",

    "sql/criar_tabelas.sql": """-- Tabela principal de utilizadores com suporte a IDs a partir de 14000, flags e perfis
CREATE TABLE IF NOT EXISTS usuarios (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    login TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    ativo INTEGER DEFAULT 1,
    liberado INTEGER DEFAULT 0,
    is_bot INTEGER DEFAULT 0,
    is_admin INTEGER DEFAULT 0,
    deve_trocar_senha INTEGER DEFAULT 0,
    origem_cadastro TEXT DEFAULT 'MANUAL'
);
"""
}

def criar_estrutura():
    print("A iniciar a criação da estrutura modular do projeto...")
    
    # Criar pastas
    for pasta in pastas:
        os.makedirs(pasta, exist_ok=True)
        print(f"Pasta criada/verificada: {pasta}/")
        
    # Criar ficheiros com conteúdo inicial
    for caminho, conteudo in ficheiros.items():
        if not os.path.exists(caminho):
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(conteudo)
            print(f"Ficheiro criado: {caminho}")
        else:
            print(f"Ficheiro já existe (ignorado): {caminho}")
            
    print("\nEstrutura configurada com sucesso!")

if __name__ == "__main__":
    criar_estrutura()