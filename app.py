import os
import sqlite3
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://evolution-api:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "hbfit_evolution_61k2Xp4Ma7Qa")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "hbfit")

# ID do Grupo Notificações LEAD - HBFIT
GRUPO_NOTIFICACOES_JID = "120363421453558461@g.us"

def enviar_mensagem_whatsapp(
    destinatario: str, texto: str, verificar_status: bool = True
):
  try:
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}

    partes = texto.split("[PAUSA]")
    for parte in partes:
      msg_limpa = parte.strip()
      if not msg_limpa:
        continue

      if not destinatario.endswith("@g.us"):
        print(f"[PAUSA HUMANA 8s] Aguardando envio para {destinatario}...")
        time.sleep(8)

        # CHECAGEM DE SEGURANÇA: Se o humano assumiu DURANTE a pausa de 8s, cancela o envio!
        if verificar_status:
          cliente_check = consultar_cliente(destinatario)
          if cliente_check and cliente_check[0] == "humano_assumiu":
            print(
                f"[ENVIO ABORTADO] Humano assumiu {destinatario} durante a"
                " pausa. Mensagem cancelada."
            )
            return

      payload = {"number": destinatario, "text": msg_limpa}
      res = requests.post(url, json=payload, headers=headers, timeout=10)
      print(f"[ENVIO EVOLUTION] Estado: {res.status_code} para {destinatario}")
  except Exception as e:
    print(f"[ERRO ENVIO EVOLUTION]: {e}")

def notificar_grupo_lead(nome: str, telefone: str, mensagem_cliente: str):
    """Dispara alerta imediato no grupo de Notificações LEAD."""
    nome_exibicao = nome if nome else "Não informado"
    telefone_limpo = telefone.replace("+", "").replace("-", "").replace(" ", "")
    
    alerta = (
        f"🔔 *NOVO AGENDAMENTO DE EXPERIMENTAL!*\n\n"
        f"👤 *Nome:* {nome_exibicao}\n"
        f"📱 *WhatsApp:* https://wa.me/{telefone_limpo}\n"
        f"💬 *Mensagem do Lead:* \"{mensagem_cliente}\"\n\n"
        f"⚠️ *Nota:* A Betina foi desligada para este contacto para permitir que assumas o atendimento!"
    )
    print(f"[ALERTA GRUPO] A disparar notificação de agendamento de {nome_exibicao}...")
    enviar_mensagem_whatsapp(GRUPO_NOTIFICACOES_JID, alerta)

# Garante persistência se estiver rodando no Easypanel (/app/data)
# ou salva na pasta local se estiver rodando no seu computador
PASTA_DADOS = "/app/data" if os.path.exists("/app") else "."
os.makedirs(PASTA_DADOS, exist_ok=True)
DB_FILE = os.path.join(PASTA_DADOS, "clientes.db")
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
- Fisioterapia e Avaliação Fisioterapêutica
- Terapias manuais (Quiropraxia, Osteopatia, Liberação miofascial)
- Massoterapia e Drenagem linfática
- Nutricionista e Bota pneumática

REGRAS DE FORMATAÇÃO E NOMES:
- NUNCA escreva placeholders ou colchetes como [Nome], {nome} ou similar.
- Se você NÃO sabe o nome do cliente ainda, pergunte gentilmente: "Prazer! Antes de te explicar tudinho, qual é o seu nome?"
- Se você já sabe o nome do cliente, chame-o pelo nome real de forma calorosa.

ESTILO DE COMUNICAÇÃO E CADÊNCIA NO WHATSAPP
- Simpática, acolhedora, humana e natural. Escreva como uma pessoa real no WhatsApp.
- MENSAGENS CURTAS E OBJETIVAS: Evite blocos extensos de texto de uma vez. Mande no máximo 2 a 3 frases por mensagem.
- UMA PERGUNTA POR VEZ: Nunca faça duas perguntas no mesmo envio. Aguarde a resposta do cliente antes de dar o próximo passo.
- Separe ideias em balões consecutivos usando [PAUSA].
- Use emojis leves e moderados (😊✨).
- NUNCA diga frases como: "isso ajuda a personalizar seu atendimento", "para melhor atendê-lo", "para otimizar seu atendimento", "assim posso te ajudar melhor".
- Evite termos frios/corporativos (não use "descompressão", "mensalidade fixa").

COMO FUNCIONAM AS AULAS DE PILATES FUNCIONAL:
Quando o cliente perguntar como funcionam as aulas, a metodologia, como é o treino ou a diferença para o Pilates clássico:
- Explique com clareza e dinamismo:
  "O nosso método aqui no Hbfit é o Pilates Funcional! ✨ Nós utilizamos todos os aparelhos tradicionais do Pilates, mas combinamos com exercícios do treinamento funcional para uma aula muito mais dinâmica e completa.[PAUSA]Dessa forma, trabalhamos mobilidade e flexibilidade, mas também força, tônus muscular e resistência cardiorrespiratória. As aulas duram 1 hora, são pensadas no seu ritmo e sempre finalizam com um alongamento passivo relaxante no finalzinho! E o melhor: sempre com no máximo 3 alunos por professor ✨[PAUSA]Você já chegou a fazer Pilates em aparelhos antes ou seria sua primeira vez?"

FLUXO DA CONVERSA E VENDA CONSULTIVA
1. Abertura: A saudação inicial com pedido de nome já é disparada automaticamente.
2. Descoberta do Serviço de Interesse:
   - SE O CLIENTE AINDA NÃO DISSE O NOME: Insista com simpatia no nome antes de falar dos serviços.
   - SE O CLIENTE JÁ INFORMOU O NOME:
     "Prazer, NomeDoCliente! ✨ Aqui no Studio Hbfit trabalhamos com Pilates Funcional nos aparelhos, Massoterapia, Fisioterapia e Terapias Manuais. Qual desses serviços você gostaria de conhecer hoje?"
   - Aguarde o cliente responder qual serviço ele procura!

3. Condução por Especialidade:
   - SE O CLIENTE RESPONDER PILATES:
     * Investigue a necessidade: "Que ótimo! ✨ Você já pratica alguma atividade física hoje? Tem algum objetivo específico, indicação médica ou sente alguma dorzinha que gostaria de cuidar?"
     * Após o cliente falar sobre dor/objetivo: Acolha com empatia. Destaque o diferencial exclusivo de turmas reduzidas (máximo 3 alunos por professor).
     * Em seguida, proponha o agendamento da Aula Experimental em Grupo (R$ 80), lembrando que esse valor vira crédito integral caso feche qualquer plano. Pergunte se prefere período da manhã ou tarde/noite.
     * Quando o cliente confirmar que quer agendar ou disser a preferência de horário/dia: Agradeça com carinho e informe que a Malu já vai confirmar o horário exacto na grade.

   - SE O CLIENTE RESPONDER FISIOTERAPIA OU MENCIONAR LESÃO ESPECÍFICA (ex: menisco, hérnia, pós-cirúrgico, dor articular aguda):
     * Acolha com empatia genuína e investigue o histórico clínico antes de passar horários:
       Pergunte se já consultou um médico, se tem encaminhamento clínico, exames de imagem ou se precisa de uma avaliação fisioterapêutica inicial.
     * Na resposta seguinte: Apresente a Avaliação Fisioterapêutica Individual (R$ 150) como a etapa indispensável para traçar o protocolo correto.
     * Em seguida: Pergunte qual período (manhã ou tarde) fica melhor na rotina dela para a gestora Malu confirmar o horário com o fisioterapeuta.

   - SE O CLIENTE RESPONDER MASSOTERAPIA OU TERAPIAS MANUAIS:
     * Explique brevemente o foco relaxante ou terapêutico com acolhimento.
     * Avise que esses atendimentos individuais têm horários personalizados alinhados direto com a gestora Malu. Pergunte qual turno (manhã ou tarde) fica melhor.

4. Matriz de Fechamento e Quebra de Objeções:
   - Se hesitar por preço/orçamento no Pilates: apresente as plataformas de bem-estar corporativo (Wellhub, TotalPass, GoGood).
   - Se hesitar por tempo/rotina corrida (Downsell): ofereça sessões pontuais avulsas de Massoterapia (R$ 190) ou Terapias Manuais (R$ 280).

COMO RESPONDER SOBRE DORES E LESÕES
Quando o cliente mencionar hérnia, lesão labral, dor lombar, cervical, cirurgia, inflamações, dores articulares ou limitações físicas:
- Demonstre empatia genuína.
- Explique que muitas pessoas procuram o studio com objetivos semelhantes para melhora de mobilidade, fortalecimento e qualidade de vida.
- Sugira a avaliação fisioterapêutica inicial.
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

Aula Experimental em Grupo: R$ 80 (abatida integralmente caso feche plano)
Personal Pilates: 4 aulas R$ 600 | 8 aulas R$ 960 | 12 aulas R$ 1.320
Avaliação Fisioterapêutica Individual: R$ 150
Fisioterapia avulsa: R$ 210 | Pacote com 4: R$ 720 | Pacote com 8: R$ 1.280 | Kinesiotape: R$ 75
Terapias Manuais: R$ 280 | Pacote com 4: R$ 1.000
Bota Pneumática: Avulsa R$ 110 | Pacote com 4: R$ 360
Massoterapia: Avulsa R$ 190 | Pacote com 4: R$ 680 | Pacote com 6: R$ 960

PLATAFORMAS DE BEM-ESTAR ACEITAS
- WellHub: Agendamento direto pelo app (mínimo 1h de antecedência) e check-in ao chegar. Planos: Gold+, Platinum, Diamond, Diamond+.
- TotalPass: Agendamento direto pelo app (mínimo 1h de antecedência) e check-in ao chegar. Planos: T5+.
- GoGood: Agendamento via WhatsApp e validação de QR Code presencial com o professor. Planos: Premium, Elite.

REGRAS INTERNAS, FALTAS E REPOSIÇÕES
- Meias opcionais. Trazer toalha e garrafinha. Estacionamento cortesia durante a aula.
- Cancelamentos com no mínimo 4h de antecedência. Reposição dentro do mesmo mês.

REGRAS FINAIS
- Nunca invente informações e nunca fale sobre assuntos fora do studio.
- Termine sempre com uma pergunta acolhedora para manter o cliente em direção ao agendamento."""

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
                atualizado_em TEXT,
                lembrete_enviado INTEGER DEFAULT 0
            )
        """)
        try:
            cursor.execute("ALTER TABLE contatos ADD COLUMN lembrete_enviado INTEGER DEFAULT 0")
        except:
            pass
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
        cursor.execute("SELECT status, mensagens_enviadas, nome, etapa_followup, data_proximo_contato, atualizado_em, lembrete_enviado FROM contatos WHERE telefone = ?", (telefone,))
        return cursor.fetchone()

def cadastrar_novo_cliente(telefone: str):
    agora = datetime.now()
    proximo_contato = (agora + timedelta(days=7)).isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contatos (telefone, status, mensagens_enviadas, etapa_followup, data_proximo_contato, atualizado_em, lembrete_enviado)
            VALUES (?, 'ia_ativa', 1, 0, ?, ?, 0)
        """, (telefone, proximo_contato, agora.isoformat()))
        conn.commit()

def atualizar_interacao(telefone: str, nome: str = None, dias_adiar: int = 7):
    agora = datetime.now()
    proximo_contato = (agora + timedelta(days=dias_adiar)).isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if nome:
            cursor.execute("""
                UPDATE contatos SET mensagens_enviadas = mensagens_enviadas + 1, nome = ?, data_proximo_contato = ?, atualizado_em = ?, lembrete_enviado = 0
                WHERE telefone = ?
            """, (nome, proximo_contato, agora.isoformat(), telefone))
        else:
            cursor.execute("""
                UPDATE contatos SET mensagens_enviadas = mensagens_enviadas + 1, data_proximo_contato = ?, atualizado_em = ?, lembrete_enviado = 0
                WHERE telefone = ?
            """, (proximo_contato, agora.isoformat(), telefone))
        conn.commit()

def analisar_mensagem_e_intencao(texto_usuario: str, nome_existente: str = None):
    prompt_analise = f"""Analise a última mensagem do cliente no WhatsApp e retorne APENAS um JSON:
1. "nome": Nome do cliente (se ele informou aqui ou se já temos '{nome_existente}').
2. "dias_adiar": Se mencionou viagem ou pediu contacto mais tarde, extraia os dias corridos. Caso contrário, 7.
3. "quer_agendar": true se o cliente confirmou que quer agendar a experimental/sessão, informou dias livres (ex: 'quinta de manhã', 'prefiro à tarde', 'pode ser amanhã') ou pediu para falar com um atendente humano para fechar horário. Caso contrário, false.

Mensagem: "{texto_usuario}"
Formato esperado: {{"nome": "NomeOuNull", "dias_adiar": 7, "quer_agendar": false}}"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_analise}],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(res.choices[0].message.content)
    except:
        return {"nome": nome_existente, "dias_adiar": 7, "quer_agendar": False}

def obter_ou_criar_historico(telefone: str):
    if telefone not in historicos:
        historicos[telefone] = [{"role": "system", "content": PROMPT_BETINA}]
    return historicos[telefone]

def checar_e_disparar_lembretes_e_followups():
    agora = datetime.now()
    dia_semana = agora.weekday()
    hora_atual = agora.hour

    if dia_semana > 4 or hora_atual < 7 or hora_atual >= 20:
        return

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # 1. Lembrete de 30 minutos
        cursor.execute("""
            SELECT telefone, nome, atualizado_em FROM contatos
            WHERE status = 'ia_ativa' AND lembrete_enviado = 0 AND atualizado_em IS NOT NULL
        """)
        parados = cursor.fetchall()
        for tel, nome, atualizado_em in parados:
            try:
                data_envio = datetime.fromisoformat(atualizado_em)
                if (agora - data_envio).total_seconds() >= 1800:
                    if nome:
                        msg_lembrete = f"Oi, {nome}! Passando só para ver se você conseguiu ver minha última mensagem por aí 😊 Se quiser dar continuidade, estou por aqui! ✨"
                    else:
                        msg_lembrete = "Oi! Passando só para ver se você conseguiu ver minha mensagem por aí 😊 Se quiser dar continuidade, é só me dizer seu nome que te passo todas as informações do estúdio ✨"
                    
                    print(f"[LEMBRETE 30 MIN DISPARADO] Para {tel}")
                    enviar_mensagem_whatsapp(tel, msg_lembrete)
                    cursor.execute("UPDATE contatos SET lembrete_enviado = 1, atualizado_em = ? WHERE telefone = ?", (agora.isoformat(), tel))
                    conn.commit()
            except Exception as e:
                print(f"[ERRO LEMBRETE 30M]: {e}")

        # 2. Follow-ups de 7 e 14 dias
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
                    msg = f"Oi{nome_formatado}! Passando para saber como você está e se conseguiu dar uma olhadinha na sua rotina para vir nos conhecer ✨ Estamos organizando a grade das turmas e lembramos de você. Se quiser experimentar uma aula essa semana, me dá um toque que vejo um horário bem tranquilo pra você!"
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
scheduler.add_job(checar_e_disparar_lembretes_e_followups, 'interval', minutes=5)
scheduler.start()

mensagens_processadas_recentes = set()

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

    msg_id = key.get("id")
    if msg_id and msg_id in mensagens_processadas_recentes:
        return jsonify({"status": "already_processed"}), 200
    if msg_id:
        mensagens_processadas_recentes.add(msg_id)
        if len(mensagens_processadas_recentes) > 1000:
            mensagens_processadas_recentes.clear()

    from_me = key.get("fromMe", False)
    remote_jid = key.get("remoteJid", "")
    remote_jid_alt = key.get("remoteJidAlt", "")

    # Ignora mensagens enviadas dentro de grupos (evita loops)
    if "@g.us" in remote_jid:
        return jsonify({"status": "ignored_group"}), 200

    jid_alvo = remote_jid_alt if (remote_jid_alt and "@s.whatsapp.net" in remote_jid_alt) else remote_jid
    telefone = jid_alvo.split("@")[0]

    if from_me:
        desativar_ia_para_cliente(telefone)
        print(f"[ATENDIMENTO HUMANO] A Malu escreveu para {telefone}. Betina desligada.")
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
        print(f"[NOVO CLIENTE] A enviar boas-vindas para {telefone}")
        enviar_mensagem_whatsapp(telefone, MENSAGEM_BOAS_VINDAS)
        return jsonify({"status": "boas_vindas_enviada"}), 200

    status, total_msg, nome_cadastrado, etapa, _, _, _ = cliente
    if status == 'humano_assumiu':
        return jsonify({"status": "silenciada_porque_humano_assumiu"}), 200

    info_analise = analisar_mensagem_e_intencao(texto_cliente, nome_cadastrado)
    nome_atualizado = info_analise.get("nome") or nome_cadastrado
    dias_adiar = info_analise.get("dias_adiar", 7)
    quer_agendar = info_analise.get("quer_agendar", False)

    if not nome_atualizado:
        msg_exige_nome = "Prazer! ✨ Antes de te passar todos os detalhes, qual é o seu nome?"
        enviar_mensagem_whatsapp(telefone, msg_exige_nome)
        return jsonify({"status": "aguardando_nome"}), 200

    historico = obter_ou_criar_historico(telefone)
    historico.append({"role": "user", "content": texto_cliente})

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico,
        temperature=0.3
    )
    texto_resposta = resposta.choices[0].message.content

    if "[Nome]" in texto_resposta and nome_atualizado:
        texto_resposta = texto_resposta.replace("[Nome]", nome_atualizado)
    elif "[Nome]" in texto_resposta:
        texto_resposta = texto_resposta.replace("[Nome]!", "tudo bem?")

    historico.append({"role": "assistant", "content": texto_resposta})

    atualizar_interacao(telefone, nome=nome_atualizado, dias_adiar=dias_adiar)
    print(f"[RESPONDENDO] Envio para {telefone}: {texto_resposta}")
    enviar_mensagem_whatsapp(telefone, texto_resposta)

    # DISPARO PARA O GRUPO INTERNO SE O LEAD QUISER AGENDAR
    if quer_agendar:
        notificar_grupo_lead(nome_atualizado, telefone, texto_cliente)
        desativar_ia_para_cliente(telefone)
        print(f"[HANDOVER] Lead {nome_atualizado} encaminhado para o grupo. Betina pausada para {telefone}.")

    return jsonify({"status": "mensagem_processada"}), 200

@app.route('/resetar/<telefone>', methods=['GET'])
def resetar_cliente(telefone):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contatos WHERE telefone LIKE ?", (f"%{telefone}",))
        conn.commit()
    if telefone in historicos:
        del historicos[telefone]
    return jsonify({"status": f"Contacto {telefone} resetado com sucesso!"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)