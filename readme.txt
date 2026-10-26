

Como usar:

    Guarde o código acima num ficheiro chamado setup_projeto.py.

    Abra o terminal nessa pasta e execute:
    Bash
------------------------------------
1 executar   python setup_projeto.py
-----------------	
	
	Não, o script executa-se apenas localmente no seu computador. Ele cria as pastas e os ficheiros na pasta do seu disco rígido.

Para que esses ficheiros apareçam no seu repositório do GitHub, precisará de enviá-los (fazer o push).

Aqui tem as formas mais simples de fazer isso:
Como enviar para o GitHub após criar os ficheiros localmente:
Opção A: Usando os Comandos Git no Terminal (Recomendado)

Se tiver o Git instalado no seu computador, 
abra o terminal na pasta do projeto e execute os seguintes comandos sequencialmente (substituindo o link pelo do seu repositório real no GitHub):
Bash
2--------------------------------------------------------------------------------------
# 1. Inicializa o repositório Git localmente
git init

# 2. Prepara todos os ficheiros criados para envio
git add .

# 3. Regista a alteração com uma mensagem
git commit -m "Estrutura inicial do projeto PoC"

# 4. Liga ao seu repositório remoto no GitHub (substitua pelo URL do seu repositório)
git remote add origin https://github.com/O_SEU_UTILIZADOR/nome-do-repositorio.git

# 5. Envia os ficheiros para o GitHub
git branch -M main
git push -u origin main
	
	