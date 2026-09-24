import sqlite3
from datetime import datetime

DB_FILE = "clientes.db"

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
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        inseridos = 0
        for tel in telefones_alunos:
            numero_limpo = "".join(filter(str.isdigit, tel))
            if numero_limpo:
                # Salva o formato normal e o formato com 55 (padrão WhatsApp)
                variacoes = [numero_limpo]
                if not numero_limpo.startswith("55"):
                    variacoes.append(f"55{numero_limpo}")
                
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
    print(f"Sucesso: {inseridos} alunos cadastrados com proteção total no banco!")

if __name__ == '__main__':
    bloquear_telefones()
