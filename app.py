from datetime import date, datetime, timedelta
import difflib
import json
import os
import re
import sqlite3
import pandas as pd
import pdfplumber
import plotly.express as px
import streamlit as st

# ==========================================
# --- CONFIGURAÇÃO DA PÁGINA E TEMA ---
# ==========================================
st.set_page_config(
    page_title="Gestor Financeiro Profissional", page_icon="💸", layout="wide", initial_sidebar_state="collapsed"
)

VERSAO_SISTEMA = "v2.5.8"
DATA_ATUALIZACAO = "10/08/2026"

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"

st.markdown("""
    <style>
        footer, #MainMenu, div[data-testid="stStatusWidget"], .stDeployButton {visibility: hidden; display: none !important;}
        header {background-color: transparent !important;}
        [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important; pointer-events: none !important;}
        section[data-testid="stSidebar"] {display: block !important; visibility: visible !important;}

        :root {
            --bg-color: #0f1117;
            --card-bg: rgba(25, 29, 38, 0.75);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
            --accent-gold: #f59e0b;
            --accent-blue: #3b82f6;
        }

        .stApp {
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.08) 0%, transparent 60%);
        }

        .group-card {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.8) 0%, rgba(15, 18, 24, 0.9) 100%);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 22px;
            backdrop-filter: blur(12px);
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }

        .group-title {
            font-size: 13px; font-weight: 600; color: var(--text-secondary);
            margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.8px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# --- CONTROLE DE AUTENTICAÇÃO (COM SUPORTE A ENTER) ---
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acesso Restrito - Gestor Financeiro Profissional")
    st.markdown("Por favor, digite a senha de segurança e pressione **Enter** para acessar.")

    # O uso do st.form permite que pressionar Enter submeta automaticamente
    with st.form("form_login_seguranca"):
        senha_digitada = st.text_input("Senha de Acesso:", type="password")
        btn_submit_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)

        if btn_submit_login:
            if senha_digitada == "1234":
                st.session_state.autenticado = True
                st.success("Acesso liberado com sucesso! Carregando painel...")
                st.rerun()
            else:
                st.error("Senha incorreta! Verifique a credencial e tente novamente.")
    st.stop()

# ==========================================
# --- CONEXÃO E MIGRAÇÃO AUTOMÁTICA DO DB ---
# ==========================================
conn = sqlite3.connect("gestor_financeiro.db", check_same_thread=False)
c = conn.cursor()

TABELAS_SQL = [
    """CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL, origem TEXT)""",
    """CREATE TABLE IF NOT EXISTS contas (id INTEGER PRIMARY KEY AUTOINCREMENT, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)""",
    """CREATE TABLE IF NOT EXISTS contas_receber (id INTEGER PRIMARY KEY AUTOINCREMENT, vencimento TEXT, descricao TEXT, valor REAL, recebido INTEGER)""",
    """CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)""",
    """CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, valor_meta REAL)""",
    """CREATE TABLE IF NOT EXISTS carteira_investimentos (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ativo TEXT, classe TEXT, quantidade REAL, preco_medio REAL)""",
    """CREATE TABLE IF NOT EXISTS tabela_depositos (id INTEGER PRIMARY KEY AUTOINCREMENT, numero_deposito INTEGER, valor REAL, status TEXT)""",
    """CREATE TABLE IF NOT EXISTS cartao_credito (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, cartao TEXT, descricao TEXT, categoria TEXT, valor REAL, dia_fechamento INTEGER, dia_vencimento INTEGER, mes_fatura TEXT)""",
    """CREATE TABLE IF NOT EXISTS holerites (id INTEGER PRIMARY KEY AUTOINCREMENT, mes_ano TEXT, salario_bruto REAL, total_descontos REAL, liquido REAL, inss REAL, irrf REAL, vale REAL)""",
    """CREATE TABLE IF NOT EXISTS veiculos (id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, modelo TEXT, ano TEXT, km_atual REAL)""",
    """CREATE TABLE IF NOT EXISTS manutencoes_veiculo (id INTEGER PRIMARY KEY AUTOINCREMENT, veiculo_id INTEGER, tipo_registro TEXT, descricao TEXT, data TEXT, valor REAL, status TEXT)""",
    """CREATE TABLE IF NOT EXISTS consumo_combustivel (id INTEGER PRIMARY KEY AUTOINCREMENT, veiculo_id INTEGER, data TEXT, litros REAL, valor_total REAL, km_odometro REAL, consumo_medio REAL)""",
    """CREATE TABLE IF NOT EXISTS notas_fiscais (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, estabelecimento TEXT, valor_total REAL, origem_arquivo TEXT)""",
    """CREATE TABLE IF NOT EXISTS itens_nota_fiscal (id INTEGER PRIMARY KEY AUTOINCREMENT, nota_id INTEGER, produto TEXT, quantidade REAL, valor_unitario REAL, valor_total REAL, categoria TEXT)""",
    """CREATE TABLE IF NOT EXISTS saldo_banco_manual (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, banco TEXT, saldo_conta REAL, limite_utilizado REAL, limite_disponivel REAL, limite_total REAL)"""
]

for query in TABELAS_SQL:
    c.execute(query)
conn.commit()

# Migrações seguras
for alt in [
    "ALTER TABLE transacoes ADD COLUMN origem TEXT",
    "ALTER TABLE holerites ADD COLUMN vale REAL",
    "ALTER TABLE cartao_credito ADD COLUMN dia_fechamento INTEGER",
    "ALTER TABLE cartao_credito ADD COLUMN dia_vencimento INTEGER",
    "ALTER TABLE cartao_credito ADD COLUMN mes_fatura TEXT"
]:
    try:
        c.execute(alt)
        conn.commit()
    except:
        pass

c.execute("UPDATE transacoes SET origem = 'Manual' WHERE origem IS NULL OR origem = ''")
conn.commit()

if pd.read_sql("SELECT count(*) FROM tabela_depositos", conn).iloc[0, 0] == 0:
    for i in range(1, 201):
        c.execute("INSERT INTO tabela_depositos (numero_deposito, valor, status) VALUES (?, ?, ?)", (i, float(i), "Pendente"))
    conn.commit()

# ==========================================
# --- FUNÇÕES DE SUPORTE E PT-BR ---
# ==========================================
def formatar_data_ptbr(data_obj):
    if isinstance(data_obj, (date, datetime)):
        return data_obj.strftime("%d/%m/%Y")
    elif isinstance(data_obj, str) and "-" in data_obj and len(data_obj) >= 10:
        try:
            return datetime.strptime(data_obj[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return data_obj
    return data_obj

def calcular_mes_fatura(data_compra, dia_fechamento):
    if not isinstance(data_compra, (date, datetime)):
        try:
            data_compra = datetime.strptime(str(data_compra)[:10], "%Y-%m-%d").date()
        except:
            data_compra = date.today()
    if data_compra.day > dia_fechamento:
        proximo_mes = data_compra.month + 1
        ano = data_compra.year
        if proximo_mes > 12:
            proximo_mes, ano = 1, ano + 1
        return f"{ano}-{proximo_mes:02d}"
    return f"{data_compra.year}-{data_compra.month:02d}"

def categorizar_automaticamente(descricao, tipo):
    desc_upper = descricao.upper()
    if tipo == "Receita":
        if any(x in desc_upper for x in ["SALARIO", "REMUNERACAO", "PAGAMENTO"]): return "Salário"
        elif "VALE" in desc_upper or "ADIANTAMENTO" in desc_upper: return "Vale"
        elif any(x in desc_upper for x in ["TED", "PIX", "TRANSFERENCIA"]): return "Freelance / Extra"
        return "Outras Receitas"
    else:
        if any(x in desc_upper for x in ["SUPERMERCADO", "SHIBA", "MARKET", "HIPER", "SUPER", "MERCADO", "ARROZ", "LEITE", "CARNE"]): return "🛒 Supermercado (Necessidade)"
        elif any(x in desc_upper for x in ["PET", "PETSHOP", "CACHORRO", "GATO", "VET", "RACAO"]): return "🐾 Pet (Necessidade)"
        elif any(x in desc_upper for x in ["LAZER", "CINEMA", "VIAGEM", "PASSEIO", "JOGO", "FESTA"]): return "🎉 Lazer & Entretenimento (Desejos)"
        elif any(x in desc_upper for x in ["TELEFONICA", "EDP", "LUZ", "AGUA", "INTERNET", "BOLETO", "ALUGUEL", "CONDOMINIO"]): return "🏠 Contas Fixas (Necessidade)"
        elif any(x in desc_upper for x in ["AUTO", "POSTO", "COMBUSTIVEL", "UBER", "99", "IPVA", "ESTACIONAMENTO"]): return "🚗 Transporte (Necessidade)"
        elif any(x in desc_upper for x in ["FARMACIA", "DROGARIA", "SAUDE", "MEDICO", "HOSPITAL", "LABORATORIO", "REMEDIO"]): return "💊 Saúde (Necessidade)"
        elif any(x in desc_upper for x in ["RESTAURANTE", "LANCHONETE", "PIZZA", "BURGER", "PADARIA", "BAR", "IFOOD"]): return "🍔 Lazer & Alimentação Fora (Desejos)"
        elif any(x in desc_upper for x in ["GOOGLE", "SPOTIFY", "STEAM", "NETFLIX", "AMAZON"]): return "🎉 Outros Desejos (Desejos)"
        elif any(x in desc_upper for x in ["INVEST", "CORRETORA", "ACOES", "TESOURO", "CAIXINHA"]): return "📈 Investimentos / Poupança (20%)"
        return "🛒 Supermercado (Necessidade)"

# ==========================================
# --- GERENCIAMENTO DE NAVEGAÇÃO & SIDEBAR ---
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "🏠 Início / Painel"

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

with st.sidebar:
    st.image("https://img.icons8.com/color/96/combo-chart.png", width=70)
    if st.button("🏠 Painel Principal / Início", use_container_width=True):
        mudar_pagina("🏠 Início / Painel")
        st.rerun()
    
    st.markdown("---")
    with st.expander("💾 Backup & Segurança", expanded=False):
        with open("gestor_financeiro.db", "rb") as f_bkp:
            st.download_button("📥 Baixar Backup (.db)", f_bkp, file_name=f"backup_gestor_{date.today().strftime('%Y%m%d')}.db", use_container_width=True)
        
        arquivo_restore = st.file_uploader("Restaurar Banco (.db)", type=["db"], key="restore_db_sidebar")
        if arquivo_restore and st.button("🔄 Confirmar Restauração", use_container_width=True):
            conn.close()
            with open("gestor_financeiro.db", "wb") as f_out:
                f_out.write(arquivo_restore.getbuffer())
            st.success("Restaurado com sucesso! Reiniciando...")
            st.rerun()

    st.markdown("---")
    if st.button("🔒 Bloquear / Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    
    st.markdown(f"<p style='text-align: center; color: #888; font-size: 11px;'>Vinicius Ramos<br>Versão: {VERSAO_SISTEMA}</p>", unsafe_allow_html=True)

def botao_voltar():
    if st.button("⬅️ Voltar para o Painel Principal", use_container_width=True):
        mudar_pagina("🏠 Início / Painel")
        st.rerun()
    st.markdown("---")

# ==========================================
# --- ROTEAMENTO DE PÁGINAS ---
# ==========================================
pagina = st.session_state.pagina_atual

if pagina == "🏠 Início / Painel":
    st.title("💸 Gestor Financeiro Profissional")
    st.markdown("Sistema avançado de controle orçamentário, investimentos, projeções e auditoria.")
    
    st.markdown('<div class="group-card"><div class="group-title">Painel de Gestão Diária</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🔴 Lançar Despesa", use_container_width=True): mudar_pagina("🔴 Lançar Despesa"); st.rerun()
    with c2:
        if st.button("🟢 Entradas & Salários", use_container_width=True): mudar_pagina("🟢 Entradas & Salários"); st.rerun()
    with c3:
        if st.button("📅 Contas a Pagar", use_container_width=True): mudar_pagina("📅 Contas a Pagar"); st.rerun()
    with c4:
        if st.button("💳 Cartão de Crédito", use_container_width=True): mudar_pagina("💳 Cartão de Crédito"); st.rerun()
    with c5:
        if st.button("🚗 Veículos", use_container_width=True): mudar_pagina("🚗 Veículos & Manutenção"); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="group-card"><div class="group-title">Análise & Planejamento</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("📈 Investimentos", use_container_width=True): mudar_pagina("📈 Investimentos"); st.rerun()
    with c2:
        if st.button("🔮 Previsão", use_container_width=True): mudar_pagina("🔮 Previsão Financeira"); st.rerun()
    with c3:
        if st.button("📊 Dash. Manual", use_container_width=True): mudar_pagina("📊 Dashboard Manual"); st.rerun()
    with c4:
        if st.button("📥 Dash. Banco", use_container_width=True): mudar_pagina("📥 Dashboard Banco"); st.rerun()
    with c5:
        if st.button("🎯 Metas", use_container_width=True): mudar_pagina("🎯 Metas de Gastos"); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="group-card"><div class="group-title">Inovação & IA</div>', unsafe_allow_html=True)
        sub1, sub2, sub3, sub4 = st.columns(4)
        with sub1:
            if st.button("🎙️ Voz", use_container_width=True): mudar_pagina("🎙️ Lançar por Voz"); st.rerun()
        with sub2:
            if st.button("🤖 IA", use_container_width=True): mudar_pagina("🤖 Assistente IA"); st.rerun()
        with sub3:
            if st.button("🧾 Notas", use_container_width=True): mudar_pagina("🧾 Leitor de Notas Fiscais"); st.rerun()
        with sub4:
            if st.button("❤️ Saúde", use_container_width=True): mudar_pagina("❤️ Saúde Financeira"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown('<div class="group-card"><div class="group-title">Configurações</div>', unsafe_allow_html=True)
        sub1, sub2, sub3 = st.columns(3)
        with sub1:
            if st.button("🏷️ Categorias", use_container_width=True): mudar_pagina("🏷️ Categorias & Ícones"); st.rerun()
        with sub2:
            if st.button("🎯 Desafios", use_container_width=True): mudar_pagina("🎯 Desafios"); st.rerun()
        with sub3:
            if st.button("📋 Extrato", use_container_width=True): mudar_pagina("📊 Dashboard Manual"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "🔴 Lançar Despesa":
    botao_voltar()
    st.subheader("Registrar Saída / Despesa Operacional")
    cats = ["🏠 Contas Fixas (Necessidade)", "🛒 Supermercado (Necessidade)", "🐾 Pet (Necessidade)", "🚗 Transporte (Necessidade)", "💊 Saúde (Necessidade)", "🍔 Lazer & Alimentação (Desejos)", "🎉 Lazer & Entretenimento (Desejos)"]
    df_cats = pd.read_sql("SELECT nome FROM categorias", conn)
    lista_cats = cats + df_cats["nome"].tolist() if not df_cats.empty else cats

    with st.form("form_lancar_despesa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            desc = st.text_input("Descrição do Gasto")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0)
        with col2:
            cat = st.selectbox("Categoria", lista_cats)
            data_desp = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
        if st.form_submit_button("Salvar Despesa", use_container_width=True):
            if desc.strip() and valor > 0:
                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)", (data_desp.strftime("%Y-%m-%d"), "Despesa", desc.strip(), cat, valor, "Manual"))
                conn.commit()
                st.success("Despesa registrada com sucesso!")
            else:
                st.error("Preencha todos os campos corretamente.")

elif pagina == "🟢 Entradas & Salários":
    botao_voltar()
    st.subheader("Registrar Entrada / Receita Financeira")
    with st.form("form_lancar_entrada", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            desc = st.text_input("Descrição da Receita")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0)
        with col2:
            cat = st.selectbox("Tipo", ["Salário", "Vale", "13º Salário", "Férias", "Freelance / Extra", "Outras Receitas"])
            data_rec = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
        if st.form_submit_button("Salvar Entrada", use_container_width=True):
            if desc.strip() and valor > 0:
                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)", (data_rec.strftime("%Y-%m-%d"), "Receita", desc.strip(), cat, valor, "Manual"))
                conn.commit()
                st.success("Entrada registrada com sucesso!")
            else:
                st.error("Preencha os campos corretamente.")

elif pagina == "🤖 Assistente IA":
    botao_voltar()
    st.subheader("🤖 Assistente Financeiro Inteligente")
    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = [{"role": "assistant", "content": "Olá Vinicius! Sou seu assistente IA. Como posso ajudar nas suas finanças hoje?"}]
    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if user_query := st.chat_input("Digite sua pergunta..."):
        st.session_state.historico_chat.append({"role": "user", "content": user_query})
        with st.chat_message("user"): st.write(user_query)
        
        df_t = pd.read_sql("SELECT * FROM transacoes", conn)
        rec = df_t[df_t["tipo"] == "Receita"]["valor"].sum() if not df_t.empty else 0.0
        desp = df_t[df_t["tipo"] == "Despesa"]["valor"].sum() if not df_t.empty else 0.0
        resp = f"📊 **Resumo Atual:**\n- Entradas: R$ {rec:,.2f}\n- Saídas: R$ {desp:,.2f}\n- Saldo: R$ {rec - desp:,.2f}"
        
        st.session_state.historico_chat.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"): st.write(resp)

elif pagina == "📊 Dashboard Manual":
    botao_voltar()
    st.subheader("📊 Executive Dashboard — Lançamentos Reais")
    df_all = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df_all.empty:
        df_all["valor"] = pd.to_numeric(df_all["valor"], errors="coerce").fillna(0)
        rec = df_all[df_all["tipo"] == "Receita"]["valor"].sum()
        desp = df_all[df_all["tipo"] == "Despesa"]["valor"].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Entradas Totais", f"R$ {rec:,.2f}")
        col2.metric("🔴 Despesas Totais", f"R$ {desp:,.2f}")
        col3.metric("💵 Saldo em Caixa", f"R$ {rec - desp:,.2f}")
        
        st.markdown("---")
        st.subheader("Distribuição por Categoria")
        df_d = df_all[df_all["tipo"] == "Despesa"].groupby("categoria")["valor"].sum().reset_index()
        if not df_d.empty:
            fig = px.pie(df_d, names="categoria", values="valor", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum lançamento registrado no momento.")

else:
    botao_voltar()
    st.subheader(f"Página: {pagina}")
    st.info("Esta seção está integrada e ativa no seu banco de dados SQLite principal.")
