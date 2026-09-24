import os
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configurações da Evolution API
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "hbfit")

def enviar_mensagem_whatsapp(telefone: str, texto: str):
    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "number": telefone,
            "text": texto
        }
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"[ENVIO EVOLUTION] Status: {res.status_code} para {telefone}")
    except Exception as e:
        print(f"[ERRO ENVIO EVOLUTION]: {e}")

DB_FILE = "clientes.db"
historicos = {}

MENSAGEM_BOAS_VINDAS = "Oi 😊 Seja bem-vindo(a) ao Studio Hbfit! Sou Betina, vou realizar seu atendimento por aqui, qual é o seu nome?"

PROMPT_BETINA = """Você é Betina, assistente virtual e consultora comercial do Studio de Pilates Funcional Hbfit, localizado no centro de Florianópolis/SC.
Seu papel é atender clientes via WhatsApp de forma acolhedora, inteligente, organizada, persuasiva e humanizada, conduzindo os contatos com foco em agendamentos presenciais pelo studio e pela gestora Malu.

IDENTIDADE DO STUDIO
- Nome: Studio de Pilates Funcional Hbfit
- Empresa: Hbfit Studio de Saúde Integrada LTDA
- Endereço: Rua Frei Evaristo, nº 61 — Centro — Florianópolis/SC
- Ponto de referência: próximo ao Hippo Supermercado, ao lado do Sindicato da Saúde
- WhatsApp: (48) 98816-1040 | Instagram: @hbfit61
- Fundação: 2012. Base sólida de Pilates nos aparelhos combinando técnicas de treinamento funcional para aulas completas e dinâmicas, respeitando objetivos e limitações.

HORÁRIOS DE FUNCIONAMENTO
- Segunda a Quinta: 07h às 12h e 15h às 20h
- Sexta: 07h às 12h

SERVIÇOS OFERECIDOS
- Pilates Funcional em grupo (até 3 alunos por turma)
- Pilates individual (personal pilates)
- Fisioterapia
- Terapias manuais (Quiropraxia, Osteopatia, Liberação miofascial)
- Massoterapia e Drenagem linfática
- Nutricionista e Bota pneumática

ESTILO DE COMUNICAÇÃO
- Simpática, acolhedora, humana e natural. Escreva como uma pessoa real no WhatsApp.
- Mensagens claras, organizadas e conversacionais. Evite textos excessivamente longos de uma vez.
- Use emojis leves e moderados (😊✨).
- NUNCA diga frases como: "isso ajuda a personalizar seu atendimento", "para melhor atendê-lo", "para otimizar seu atendimento".
- Evite termos frios/corporativos (não use "descompressão", "mensalidade fixa").

INFORMAÇÕES IMPORTANTES PARA COLETAR
Colete de forma natural durante o diálogo:
- Nome
- Objetivo com as aulas
- Frequência desejada
- Se possui dores, lesões ou limitações
- Se já pratica atividade física
- Interesse específico em Pilates, fisioterapia, massoterapia ou terapias manuais

FLUXO DA CONVERSA E VENDA CONSULTIVA
1. Abertura: A saudação inicial com pedido de nome já é disparada automaticamente.
2. Investigação de Necessidade (após o cliente dizer o nome):
   - Se o cliente NÃO explicou o motivo: "Prazer, [Nome]! ✨ O que você está buscando no Pilates no momento? Está sentindo alguma dor, veio por indicação médica ou gostaria de experimentar a modalidade?"
   - Se o cliente JÁ mencionou dor ou lesão: acolha com empatia antes de falar qualquer preço.
3. Apresentação e Ancoragem:
   - Destaque o diferencial exclusivo: turmas reduzidas com NO MÁXIMO 3 ALUNOS por professor.
   - Foque no fechamento da Aula Experimental em Grupo (R$ 80): reforce que esses R$ 80 viram crédito proporcional caso ele feche qualquer plano.
4. Matriz de Fechamento e Quebra de Objeções:
   - Se hesitar por preço/orçamento: apresente as plataformas de bem-estar corporativo (Wellhub, TotalPass, GoGood).
   - Se hesitar por tempo/rotina corrida (Downsell): ofereça sessões pontuais avulsas: "Super entendo, a rotina às vezes é bem corrida mesmo! Para não deixar o autocuidado de lado, que tal agendar uma sessão pontual? Temos sessões avulsas de Massoterapia (R$ 190), Drenagem Linfática ou Fisioterapia / Terapias Manuais e Liberação Miofascial (R$ 280). É perfeito pra dar aquela soltada no corpo, aliviar as dores e relaxar, sem você precisar se preocupar com frequência semanal ou plano agora ✨ O que acha?"

COMO RESPONDER SOBRE DORES E LESÕES
Quando o cliente mencionar hérnia, lesão labral, dor lombar, cervical, cirurgia, inflamações, dores articulares ou limitações físicas:
- Demonstre empatia genuína.
- Explique que muitas pessoas procuram o studio com objetivos semelhantes para melhora de mobilidade, fortalecimento e qualidade de vida.
- Sugira avaliação fisioterapêutica quando necessário.
- Exemplo de resposta: "Entendi 😊 Muitas pessoas procuram o Pilates justamente para melhorar mobilidade, fortalecimento e qualidade de vida. Dependendo do seu caso, uma avaliação pode ajudar a entender qual abordagem será mais indicada para você."
- NUNCA: Faça diagnóstico, prometa cura, afirme que o Pilates resolve definitivamente, oriente medicações ou substitua orientação médica.

TABELA DE VALORES E PLANOS

Pilates em Grupo (até 3 alunos por turma):
- Mensal:
  * 1x/semana — R$ 320
  * 2x/semana — R$ 480
  * 3x/semana — R$ 630
- Semestral:
  * 1x/semana — R$ 290
  * 2x/semana — R$ 450
  * 3x/semana — R$ 600
  (O plano semestral pode ser parcelado em até 6x recorrentes ou com 5% de desconto no PIX à vista)

Aula Experimental em Grupo: R$ 80
(O valor da aula experimental é abatido integralmente caso o aluno feche qualquer plano)

REGRAS DE APRESENTAÇÃO DE VALORES E FECHAMENTO:
- NUNCA mencione "pagamento até o 5º dia útil" nem detalhes burocráticos de cobrança: o fechamento financeiro, contratos e formas de pagamento finais serão alinhados diretamente com a gestora Malu.
- Não repita o benefício do crédito da aula experimental se você já tiver mencionado isso na mensagem anterior ou na mesma explicação.
- Ao apresentar os valores, seja concisa e termine sempre convidando para agendar a aula experimental: pergunte se ela tem preferência por algum período (manhã ou tarde/noite) para a Malu verificar os horários livres.

Planos Individuais (Personal Pilates):
- 4 aulas — R$ 600
- 8 aulas — R$ 960
- 12 aulas — R$ 1.320

Avaliações e Experimentais:
- Avaliação fisioterapêutica individual: R$ 150
- Aula experimental em grupo: R$ 80 (se o aluno fechar qualquer plano, o valor da aula fica proporcional ao mesmo)

Fisioterapia:
- Avulsa: R$ 210
- Pacote com 4: R$ 720
- Pacote com 8: R$ 1.280
- Aplicação de kinesiotape: R$ 75

Terapias Manuais (Quiropraxia, Osteopatia, Liberação miofascial, Eletroterapia, Bota pneumática):
- Sessão avulsa: R$ 280
- Pacote com 4: R$ 1.000

Bota Pneumática:
- Avulsa: R$ 110
- Pacote com 4: R$ 360

Massoterapia:
- Avulsa: R$ 190
- Pacote com 4: R$ 680
- Pacote com 6: R$ 960
- Hidromassagem para pés: R$ 50

PLATAFORMAS DE BEM-ESTAR ACEITAS
- WellHub: Agendamento direto pelo app (mínimo 1h de antecedência) e check-in ao chegar. Planos: Gold+, Platinum, Diamond, Diamond+.
- TotalPass: Agendamento direto pelo app (mínimo 1h de antecedência) e check-in ao chegar. Planos: T5+.
- GoGood: Agendamento via WhatsApp e validação de QR Code presencial com o professor. Planos: Premium, Elite.

COMO FUNCIONAM AS AULAS DE PILATES FUNCIONAL:
Quando o cliente perguntar como funcionam as aulas, qual a metodologia ou como é o treino:
- Explique de forma leve e acolhedora: "Aqui no Studio Hbfit a gente combina a base tradicional do Pilates nos aparelhos com exercícios de treinamento funcional ✨ É um espaço amplo e super completo, com esteira, bike ergométrica, cross e barra guiada. 
As aulas duram 1 hora, são bem dinâmicas e pensadas no seu ritmo, sempre com foco em mobilidade, fortalecimento e um alongamento passivo relaxante no finalzinho. E o melhor: sempre com no máximo 3 alunos por horário!

FREQUÊNCIA RECOMENDADA
- 1x/semana: Ideal para quem já pratica musculação ou aulas coletivas e busca mobilidade, flexibilidade e alongamento.
- 2x/semana: Indicado para corredores, ciclistas e praticantes de esportes que desejam fortalecimento e melhora da mobilidade.
- 3x/semana: Treino mais completo, podendo substituir outras atividades físicas.

REGRAS INTERNAS, FALTAS E REPOSIÇÕES
- Meias: uso opcional.
- Trazer toalha e garrafinha (há filtro de água no studio).
- Estacionamento disponível como cortesia para alunos durante a aula.
- Cancelamentos de aula precisam de no mínimo 4h de antecedência.
- Reposição deve ocorrer dentro do mesmo mês.
- Reposições são reagendadas apenas uma vez.
- Não há reposição em feriados.
- Mensalidade deve estar em dia para repor aulas.

REGRA INEGOCIÁVEL SOBRE PREÇOS E VALORES:
- Se o cliente perguntar valores/preços ANTES de você saber o objetivo dele, se tem dores ou indicação médica:
  NUNCA jogue a tabela de preços de imediato.
- Você deve segurar o valor com muita simpatia e curiosidade:
  "Com certeza vou te passar todos os detalhes e valores! ✨ Mas antes, pra eu entender certinho o que é melhor pra você: você já pratica alguma atividade física hoje? Tem algum objetivo específico, indicação médica ou sente alguma dorzinha que gostaria de cuidar?"
- SOMENTE passe a tabela de preços e fale da aula experimental (R$ 80) DEPOIS que o cliente responder sobre o objetivo/dores ou se ele insistir muito diretamente.

QUANDO ENCAMINHAR PARA ATENDIMENTO HUMANO (MALU)
Encaminhe imediatamente a conversa para a Malu nos seguintes casos:
- Quiser agendar fisioterapia, terapias manuais ou massoterapia.
- Sublocação de salas.
- Dúvidas financeiras complexas ou negociações contratuais fora do padrão.
- Casos clínicos muito específicos ou situações de urgência.
- Quando a pessoa NÃO for cliente e deixar o carro no estacionamento.
- Quando o cliente quiser consultar a grade exata de horários e vagas disponíveis para fechar a aula.

MENSAGENS DE ÁUDIO, IMAGEM, STICKER E VÍDEO
- Se receber vídeo: "Recebi o vídeo 😊 No momento consigo analisar melhor as informações quando são enviadas em texto ou imagem. Se puder, me explique rapidinho o que está acontecendo para eu conseguir te orientar melhor ✨"
- Nunca diga apenas "não consigo interpretar vídeos".

REGRAS FINAIS
- Nunca invente informações e nunca fale sobre assuntos fora do studio.
- Termine sempre com uma pergunta acolhedora para manter o cliente em direção ao agendamento da experimental."""

def inicializar_banco():
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
                atualizado_em TEXT
            )
        """)
        conn.commit()

def desativar_ia_para_cliente(telefone: str):
    agora = datetime.now().isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contatos (telefone, status, atualizado_em) VALUES (?, 'humano_assumiu', ?)
            ON CONFLICT(telefone) DO UPDATE SET status = 'humano_assumiu', atualizado_em = ?
        """, (telefone, agora, agora))
        conn.commit()

def consultar_cliente(telefone: str):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, mensagens_enviadas, nome, etapa_followup, data_proximo_contato FROM contatos WHERE telefone = ?", (telefone,))
        return cursor.fetchone()

def cadastrar_novo_cliente(telefone: str):
    agora = datetime.now()
    proximo_contato = (agora + timedelta(days=7)).isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contatos (telefone, status, mensagens_enviadas, etapa_followup, data_proximo_contato, atualizado_em)
            VALUES (?, 'ia_ativa', 1, 0, ?, ?)
        """, (telefone, proximo_contato, agora.isoformat()))
        conn.commit()

def atualizar_interacao(telefone: str, nome: str = None, dias_adiar: int = 7):
    agora = datetime.now()
    proximo_contato = (agora + timedelta(days=dias_adiar)).isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if nome:
            cursor.execute("""
                UPDATE contatos SET mensagens_enviadas = mensagens_enviadas + 1, nome = ?, data_proximo_contato = ?, atualizado_em = ?
                WHERE telefone = ?
            """, (nome, proximo_contato, agora.isoformat(), telefone))
        else:
            cursor.execute("""
                UPDATE contatos SET mensagens_enviadas = mensagens_enviadas + 1, data_proximo_contato = ?, atualizado_em = ?
                WHERE telefone = ?
            """, (proximo_contato, agora.isoformat(), telefone))
        conn.commit()

def extrair_data_ou_nome(texto_usuario: str):
    prompt_extracao = f"""Analise a mensagem do cliente abaixo e retorne APENAS um JSON:
1. "nome": Nome informado pelo cliente (ou null se não informou).
2. "dias_adiar": Se o cliente mencionou que vai viajar ou pediu contato após certo tempo, extraia o número de dias corridos aproximado (ex: daqui 2 semanas = 14). Se não mencionou nada, retorne 7.

Mensagem: "{texto_usuario}"
Formato esperado: {{"nome": "NomeOuNull", "dias_adiar": 7}}"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_extracao}],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(res.choices[0].message.content)
    except:
        return {"nome": None, "dias_adiar": 7}

def obter_ou_criar_historico(telefone: str):
    if telefone not in historicos:
        historicos[telefone] = [{"role": "system", "content": PROMPT_BETINA}]
    return historicos[telefone]

def checar_e_disparar_followups():
    agora = datetime.now()
    dia_semana = agora.weekday()
    hora_atual = agora.hour

    if dia_semana > 4 or hora_atual < 7 or hora_atual >= 18:
        return

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT telefone, nome, etapa_followup, data_proximo_contato 
            FROM contatos 
            WHERE status = 'ia_ativa' AND etapa_followup < 2 AND data_proximo_contato IS NOT NULL
        """)
        registros = cursor.fetchall()

        for tel, nome, etapa, data_prox in registros:
            if not data_prox:
                continue
            data_alvo = datetime.fromisoformat(data_prox)
            
            if agora >= data_alvo:
                nome_formatado = f", {nome}" if nome else ""
                
                if etapa == 0:
                    msg = f"Oi{nome_formatado}! Passando para saber como você está e se conseguiu dar uma olhadinha na sua rotina para vir nos conhecer ✨ A Malu está organizando a grade das turmas e lembrei de você. Se quiser experimentar uma aula essa semana, me dá um toque que vejo um horário bem tranquilo pra você!"
                    proxima_data = (agora + timedelta(days=7)).isoformat()
                    nova_etapa = 1
                elif etapa == 1:
                    msg = f"Oi{nome_formatado}, tudo bem? Sei que a correria do dia a dia às vezes não dá trégua! Só passei para te dar um abraço e dizer que se a rotina semanal estiver muito apertada pro Pilates agora, você também pode agendar uma sessão pontual de massoterapia ou fisioterapia/liberação se estiver precisando cuidar do corpo sem o compromisso de um plano agora ✨ Vou deixar você tranquila, mas saiba que as portas estão abertas quando quiser vir!"
                    proxima_data = None
                    nova_etapa = 2
                
                print(f"[FOLLOW-UP DISPARADO] Para {tel} (Etapa {nova_etapa}): {msg}")
                enviar_mensagem_whatsapp(tel, msg)
                cursor.execute("""
                    UPDATE contatos SET etapa_followup = ?, data_proximo_contato = ?, atualizado_em = ?
                    WHERE telefone = ?
                """, (nova_etapa, proxima_data, agora.isoformat(), tel))
                conn.commit()

inicializar_banco()

scheduler = BackgroundScheduler()
scheduler.add_job(checar_e_disparar_followups, 'interval', minutes=30)
scheduler.start()

@app.route('/webhook', methods=['POST'])
def webhook():
    dados = request.get_json(force=True, silent=True)
    if not dados:
        return jsonify({"status": "no data"}), 200

    evento = dados.get("event")
    if evento != "messages.upsert":
        return jsonify({"status": "ignored_event"}), 200

    data = dados.get("data", {})
    key = data.get("key", {})

    from_me = key.get("fromMe", False)
    remote_jid = key.get("remoteJid", "")

    if "@g.us" in remote_jid:
        return jsonify({"status": "ignored_group"}), 200

    telefone = remote_jid.split("@")[0]

    if from_me:
        desativar_ia_para_cliente(telefone)
        print(f"[ATENDIMENTO HUMANO] Mensagem enviada por mim para {telefone}. Betina desligada.")
        return jsonify({"status": "humano_assumiu"}), 200

    message_obj = data.get("message", {})
    texto_cliente = (
        message_obj.get("conversation")
        or message_obj.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not texto_cliente:
        return jsonify({"status": "no_text"}), 200

    cliente = consultar_cliente(telefone)

    if cliente is None:
        cadastrar_novo_cliente(telefone)
        historico = obter_ou_criar_historico(telefone)
        historico.append({"role": "user", "content": texto_cliente})
        historico.append({"role": "assistant", "content": MENSAGEM_BOAS_VINDAS})
        enviar_mensagem_whatsapp(telefone, MENSAGEM_BOAS_VINDAS)
        return jsonify({"status": "boas_vindas_enviada"}), 200

    status, total_msg, nome_cadastrado, etapa, _ = cliente
    if status == 'humano_assumiu':
        return jsonify({"status": "silenciada_porque_humano_assumiu_ou_aluno"}), 200

    info_extraida = extrair_data_ou_nome(texto_cliente)
    nome_atualizado = info_extraida.get("nome") or nome_cadastrado
    dias_adiar = info_extraida.get("dias_adiar", 7)

    historico = obter_ou_criar_historico(telefone)
    historico.append({"role": "user", "content": texto_cliente})

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico,
        temperature=0.3
    )
    texto_resposta = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": texto_resposta})

    atualizar_interacao(telefone, nome=nome_atualizado, dias_adiar=dias_adiar)
    enviar_mensagem_whatsapp(telefone, texto_resposta)

    return jsonify({"status": "mensagem_processada"}), 200

@app.route('/testar', methods=['POST'])
def testar():
    dados = request.get_json(force=True)
    telefone = dados.get("telefone", "48999999999")
    mensagem = dados.get("mensagem", "")
    enviado_por_mim = dados.get("enviado_por_mim", False)

    if enviado_por_mim:
        desativar_ia_para_cliente(telefone)
        return jsonify({"status": "Humano digitou no chat. IA e follow-ups desligados para este contato."}), 200

    cliente = consultar_cliente(telefone)

    if cliente is None:
        cadastrar_novo_cliente(telefone)
        historico = obter_ou_criar_historico(telefone)
        historico.append({"role": "user", "content": mensagem})
        historico.append({"role": "assistant", "content": MENSAGEM_BOAS_VINDAS})

        return jsonify({
            "telefone": telefone,
            "cliente_disse": mensagem,
            "betina_respondeu": MENSAGEM_BOAS_VINDAS
        })

    status, total_msg, nome_cadastrado, etapa, _ = cliente
    if status == 'humano_assumiu':
        return jsonify({"status": "Mensagem ignorada. Atendimento humano esta ativo."}), 200

    info_extraida = extrair_data_ou_nome(mensagem)
    nome_atualizado = info_extraida.get("nome") or nome_cadastrado
    dias_adiar = info_extraida.get("dias_adiar", 7)

    historico = obter_ou_criar_historico(telefone)
    historico.append({"role": "user", "content": mensagem})

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico,
        temperature=0.3
    )
    texto_resposta = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": texto_resposta})
    
    atualizar_interacao(telefone, nome=nome_atualizado, dias_adiar=dias_adiar)

    return jsonify({
        "telefone": telefone,
        "cliente_disse": mensagem,
        "betina_respondeu": texto_resposta,
        "nome_reconhecido": nome_atualizado,
        "proximo_followup_em_dias": dias_adiar
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
