-- Tabela principal de utilizadores com suporte a IDs a partir de 14000, flags e perfis
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
