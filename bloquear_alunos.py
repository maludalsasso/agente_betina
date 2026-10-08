import os
import sqlite3
from datetime import datetime

# Garante o mesmo caminho usado pelo app.py na VPS ou local
PASTA_DADOS = "/app/data" if os.path.exists("/app/data") else "."
DB_FILE = os.path.join(PASTA_DADOS, "clientes.db")

telefones_alunos = [
    "48988379988",
    "48998159557",
    "4899803289",
    "4899696157",
    "4888232788",
    "4899540808",
    "4891190221",
    "4898403964",
    "4888449071",
    "4899471032",
    "4899691776",
    "4899548381",
    "4896010444",
    "4884026999",
    "4896160474",
    "4899724481",
    "4891766911",
    "4884814829",
    "51993234183",
    "4899722717",
    "4899117080",
    "4999117080",
    "4899614817",
    "4899870826",
    "4891300184",
    "4899829882",
    "4899493399",
    "4899055110",
    "4896160471",
    "4896222921",
    "4891052858",
    "4899816464",
    "4899602850",
    "4891561757",
    "4799924363",
    "4899303200",
    "4899479828",
    "4884039771",
    "4896177244",
    "48991442177",
    "48988270022",
    "48996995494",
    "48996383836",
    "48991727658",
    "48999711989",
    "48999140369",
    "48999731974",
    "48996289609",
    "48996169666",
    "48991572205",
    "48988079516",
    "41984206497",
    "48996606431"
]

def bloquear_telefones():
    agora = datetime.now().isoformat()
    
    # Garante que a tabela exista se o banco for novo
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contatos (
                telefone TEXT PRIMARY KEY,
                nome TEXT,
                status TEXT DEFAULT 'ia_ativa',
                mensagens_enviadas INTEGER DEFAULT 0,
                etapa_followup INTEGER DEFAULT 0,
                data_proximo_contato TEXT,
                atualizado_em TEXT,
                lembrete_enviado INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        inseridos = 0
        for tel in telefones_alunos:
            numero_limpo = "".join(filter(str.isdigit, tel))
            if not numero_limpo:
                continue

            # Retira o 55 se já tiver
            if numero_limpo.startswith("55"):
                numero_limpo = numero_limpo[2:]

            ddd = numero_limpo[:2]
            corpo = numero_limpo[2:]
            
            # Pega sempre os últimos 8 dígitos
            ultimos_8 = corpo[-8:]

            # Cria variações: com 9, sem 9, com 55 e só os 8 dígitos
            variacoes = {
                numero_limpo,
                f"55{numero_limpo}",
                ultimos_8,
                f"{ddd}9{ultimos_8}",
                f"55{ddd}9{ultimos_8}",
                f"{ddd}{ultimos_8}",
                f"55{ddd}{ultimos_8}"
            }

            for n in variacoes:
                cursor.execute("""
                    INSERT INTO contatos (telefone, status, etapa_followup, atualizado_em)
                    VALUES (?, 'humano_assumiu', 2, ?)
                    ON CONFLICT(telefone) DO UPDATE SET 
                        status = 'humano_assumiu',
                        etapa_followup = 2,
                        atualizado_em = ?
                """, (n, agora, agora))
                inseridos += 1
        
        conn.commit()
    print(f"Sucesso: {inseridos} formatos de números bloqueados no banco ({DB_FILE})!")

if __name__ == '__main__':
    bloquear_telefones()