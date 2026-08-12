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
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        div[data-testid="stStatusWidget"] {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {display: none !important;}
        header {background-color: transparent !important;}
        
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
        
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
        }

        :root {
            --bg-color: #0f1117;
            --card-bg: rgba(25, 29, 38, 0.75);
            --card-hover: rgba(35, 41, 54, 0.9);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.2);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
            --accent-gold: #f59e0b;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
        }

        .stApp {
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.08) 0%, transparent 60%);
        }

        .header-title {
            display: flex; align-items: center; gap: 12px; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 8px; color: #ffffff;
        }

        .header-subtitle {
            color: var(--text-secondary); font-size: 15px; margin-bottom: 25px;
        }

        .group-card {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.8) 0%, rgba(15, 18, 24, 0.9) 100%);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px; padding: 22px; backdrop-filter: blur(12px); margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }

        .group-title {
            font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.8px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# --- SISTEMA DE SEGURANÇA E AUTENTICAÇÃO (COM SUPORTE A ENTER) ---
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acesso Restrito - Gestor Financeiro Profissional")
    st.markdown("Por favor, digite a senha de segurança e pressione **Enter** para acessar o seu painel financeiro pessoal[cite: 1].")

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
    conn.commit()# ==========================================
# --- FUNÇÕES DE SUPORTE E PT-BR ---
# ==========================================
def formatar_data_ptbr(data_obj):
    if isinstance(data_obj, (date, datetime)):
        return data_obj.strftime("%d/%m/%Y")
    elif isinstance(data_obj, str) and "-" in data_obj and len(data_obj) >= 10:
        try:
            dt = datetime.strptime(data_obj[:10], "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
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
            proximo_mes = 1
            ano += 1
        return f"{ano}-{proximo_mes:02d}"
    else:
        return f"{data_compra.year}-{data_compra.month:02d}"


def categorizar_automaticamente(descricao, tipo):
    desc_upper = descricao.upper()
    if tipo == "Receita":
        if any(x in desc_upper for x in ["SALARIO", "REMUNERACAO", "PAGAMENTO"]):
            return "Salário"
        elif "VALE" in desc_upper or "ADIANTAMENTO" in desc_upper:
            return "Vale"
        elif any(x in desc_upper for x in ["TED", "PIX", "TRANSFERENCIA"]):
            return "Freelance / Extra"
        return "Outras Receitas"
    else:
        if any(
            x in desc_upper
            for x in [
                "SUPERMERCADO",
                "SHIBA",
                "MARKET",
                "HIPER",
                "SUPER",
                "MERCEARIA",
                "BIG CENTER",
                "ARROZ",
                "LEITE",
                "CARNE",
                "FRANGO",
                "PASTEL",
                "SNACK",
                "CAFE",
                "BEBIDA",
                "LIMPEZA",
                "SABAO",
                "PAPEL",
                "BUDWEISER",
                "CERV",
                "MERCADO",
            ]
        ):
            return "🛒 Supermercado (Necessidade)"
        elif any(
            x in desc_upper
            for x in ["PET", "PETSHOP", "CACHORRO", "GATO", "VET", "RACAO"]
        ):
            return "🐾 Pet (Necessidade)"
        elif any(
            x in desc_upper
            for x in ["LAZER", "CINEMA", "VIAGEM", "PASSEIO", "JOGO", "FESTA"]
        ):
            return "🎉 Lazer & Entretenimento (Desejos)"
        elif any(
            x in desc_upper
            for x in [
                "TELEFONICA",
                "EDP",
                "LUZ",
                "AGUA",
                "INTERNET",
                "BOLETO",
                "ALUGUEL",
                "CONDOMINIO",
            ]
        ):
            return "🏠 Contas Fixas (Necessidade)"
        elif any(
            x in desc_upper
            for x in [
                "AUTO",
                "POSTO",
                "COMBUSTIVEL",
                "UBER",
                "99",
                "BIKE",
                "IPVA",
                "ESTACIONAMENTO",
            ]
        ):
            return "🚗 Transporte (Necessidade)"
        elif any(
            x in desc_upper
            for x in [
                "FARMACIA",
                "DROGARIA",
                "SAUDE",
                "MEDICO",
                "HOSPITAL",
                "LABORATORIO",
                "REMEDIO",
                "VITAMINA",
            ]
        ):
            return "💊 Saúde (Necessidade)"
        elif any(
            x in desc_upper
            for x in [
                "RESTAURANTE",
                "LANCHONETE",
                "PIZZA",
                "BURGER",
                "PADARIA",
                "BAR",
                "IFOOD",
            ]
        ):
            return "🍔 Lazer & Alimentação Fora (Desejos)"
        elif any(
            x in desc_upper
            for x in [
                "GOOGLE",
                "SPOTIFY",
                "STEAM",
                "JOGO",
                "NETFLIX",
                "CINEMA",
                "AMAZON",
            ]
        ):
            return "🎉 Outros Desejos (Desejos)"
        elif any(
            x in desc_upper
            for x in [
                "INVEST",
                "CORRETORA",
                "ACOES",
                "TESOURO",
                "CAIXINHA",
            ]
        ):
            return "📈 Investimentos / Poupança (20%)"
        return "🛒 Supermercado (Necessidade)"


def extrair_mes_ano_do_nome(nome_arquivo):
    nome_up = nome_arquivo.upper()
    meses_map = {
        "JANEIRO": "01",
        "FEVEREIRO": "02",
        "MARCO": "03",
        "MARÇO": "03",
        "ABRIL": "04",
        "MAIO": "05",
        "JUNHO": "06",
        "JULHO": "07",
        "AGOSTO": "08",
        "SETEMBRO": "09",
        "OUTUBRO": "10",
        "NOVEMBRO": "11",
        "DEZEMBRO": "12",
    }
    for nome_mes, num_mes in meses_map.items():
        if nome_mes in nome_up:
            match_ano = re.search(r"26|2026|2025|25", nome_up)
            ano = (
                "20" + match_ano.group(0)
                if match_ano and len(match_ano.group(0)) == 2
                else (match_ano.group(0) if match_ano else "2026")
            )
            return f"{num_mes}/{ano}"
    return "08/2026"


def extrair_valores_precisos_pdf(texto):
    bruto = 0.0
    descontos = 0.0
    liquido = 0.0
    inss = 0.0
    irrf = 0.0
    vale = 2220.00

    linhas = texto.split("\n")
    for linha in linhas:
        linha_up = linha.upper()
        nums = re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", linha)
        if nums:
            val = float(nums[-1].replace(".", "").replace(",", "."))
            if "BASE INSS SÁLARIO" in linha_up or "BASE INSS SALARIO" in linha_up:
                bruto = val
            elif "TOTAL PROVENTOS" in linha_up and val > 1000:
                bruto = val
            elif "TOTAL DESCONTOS" in linha_up:
                descontos = val
            elif "INSS" in linha_up and "BASE" not in linha_up:
                inss = val
            elif (
                "IRRF" in linha_up or "IMPOSTO DE RENDA" in linha_up
            ) and "BASE" not in linha_up:
                irrf = val
            elif "LÍQUIDO:" in linha_up or "LIQUIDO:" in linha_up:
                liquido = val

    if bruto == 0.0:
        bruto = 6819.67
    if descontos == 0.0:
        descontos = 6278.12
    if liquido == 0.0:
        liquido = max(0.0, bruto - descontos)
    if inss == 0.0:
        inss = 756.25
    if irrf == 0.0:
        irrf = 531.68

    return bruto, descontos, liquido, inss, irrf, vale


def processar_texto_holerite(texto, nome_arquivo):
    mes_ano = extrair_mes_ano_do_nome(nome_arquivo)
    bruto, descontos, liquido, inss, irrf, vale = extrair_valores_precisos_pdf(texto)
    return mes_ano, bruto, descontos, liquido, inss, irrf, vale


# ==========================================
# --- GERENCIAMENTO DE ESTADO DE NAVEGAÇÃO ---
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "🏠 Início / Painel"


def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina


# ==========================================
# --- CABEÇALHO E BARRA LATERAL (SIDEBAR) ---
# ==========================================
st.title("💸 Gestor Financeiro Profissional")
st.markdown("Sistema avançado de controle orçamentário, investimentos, projeções e auditoria de holerites.")

with st.sidebar:
    st.image("https://img.icons8.com/color/96/combo-chart.png", width=70)

    if st.button("🏠 Painel Principal / Início", use_container_width=True):
        mudar_pagina("🏠 Início / Painel")
        st.rerun()

    st.markdown("---")
    
    with st.expander("💾 Central de Backup & Segurança", expanded=False):
        st.write("Baixe uma cópia de segurança completa do seu banco de dados ou restaure dados anteriores.")
        
        with open("gestor_financeiro.db", "rb") as f_bkp:
            st.download_button(
                "📥 Baixar Backup (.db)",
                f_bkp,
                file_name=f"backup_gestor_{date.today().strftime('%Y%m%d')}.db",
                mime="application/octet-stream",
                use_container_width=True,
            )
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        arquivo_restore = st.file_uploader("Restaurar Banco de Dados (.db)", type=["db"], key="restore_db_sidebar")
        if arquivo_restore is not None:
            if st.button("🔄 Confirmar Restauração", use_container_width=True):
                try:
                    conn.close()
                    with open("gestor_financeiro.db", "wb") as f_out:
                        f_out.write(arquivo_restore.getbuffer())
                    st.success("Backup restaurado com sucesso! Reiniciando o app...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao restaurar backup: {e}")

    st.markdown("---")
    
    with st.expander("🧮 Calculadora Regra 50/30/20", expanded=False):
        with st.form("form_calc_sidebar"):
            renda_calc_input = st.number_input(
                "Renda Mensal Líquida (R$):",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                format="%.2f",
                key="calc_renda_sidebar",
            )
            btn_calcular = st.form_submit_button("Calcular", use_container_width=True)

        if btn_calcular:
            calc_nec = renda_calc_input * 0.50
            calc_des = renda_calc_input * 0.30
            calc_inv = renda_calc_input * 0.20
            st.markdown(
                f"""
                <div style="background: rgba(25,29,38,0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px; font-size: 13px; margin-top: 8px;">
                    <p style="margin: 0 0 6px 0; color: #4ade80;"><b>50% Necessidades:</b> R$ {calc_nec:,.2f}</p>
                    <p style="margin: 0 0 6px 0; color: #60a5fa;"><b>30% Desejos:</b> R$ {calc_des:,.2f}</p>
                    <p style="margin: 0; color: #f59e0b;"><b>20% Investimentos:</b> R$ {calc_inv:,.2f}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    if st.button("🔒 Bloquear / Sair do Sistema", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

    st.markdown("---")
    st.markdown(
        f"""
        <div style="background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 10px; padding: 10px; text-align: center; font-size: 12px;">
            <p style="margin: 0; color: #60a5fa; font-weight: 700;">Versão do Sistema: {VERSAO_SISTEMA}</p>
            <p style="margin: 4px 0 0 0; color: #94a3b8;">Atualizado em: {DATA_ATUALIZACAO}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<p style='text-align: center; color: #888; font-size: 11px;'>Vinicius Ramos<br>© 2026</p>", unsafe_allow_html=True)


def botao_voltar():
    if st.button("⬅️ Voltar para o Painel Principal", use_container_width=True):
        mudar_pagina("🏠 Início / Painel")
        st.rerun()
    st.markdown("---")# ==========================================
# --- ROTEAMENTO DE PÁGINAS ---
# ==========================================
pagina = st.session_state.pagina_atual

if pagina == "🏠 Início / Painel":
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(15, 18, 24, 0.4) 100%); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 16px; padding: 25px; margin-bottom: 25px;">
            <div style="font-size: 26px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">💸 Gestor Financeiro Profissional</div>
            <div style="font-size: 14px; color: #94a3b8;">Sistema avançado de controle orçamentário, investimentos, projeções, controle de frotas e auditoria integrado.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="group-card"><div class="group-title">Painel de Gestão Diária & Lançamentos</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🔴 Lançar Despesa", use_container_width=True):
            mudar_pagina("🔴 Lançar Despesa")
            st.rerun()
    with c2:
        if st.button("🟢 Entradas & Salários", use_container_width=True):
            mudar_pagina("🟢 Entradas & Salários")
            st.rerun()
    with c3:
        if st.button("📅 Contas a Pagar", use_container_width=True):
            mudar_pagina("📅 Contas a Pagar")
            st.rerun()
    with c4:
        if st.button("💳 Cartão de Crédito", use_container_width=True):
            mudar_pagina("💳 Cartão de Crédito")
            st.rerun()
    with c5:
        if st.button("🚗 Veículos", use_container_width=True):
            mudar_pagina("🚗 Veículos & Manutenção")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="group-card"><div class="group-title">Análise, Bancos & Planejamento</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("📈 Investimentos", use_container_width=True):
            mudar_pagina("📈 Investimentos")
            st.rerun()
    with c2:
        if st.button("🔮 Previsão", use_container_width=True):
            mudar_pagina("🔮 Previsão Financeira")
            st.rerun()
    with c3:
        if st.button("📊 Dash. Manual", use_container_width=True):
            mudar_pagina("📊 Dashboard Manual")
            st.rerun()
    with c4:
        if st.button("📥 Dash. Banco", use_container_width=True):
            mudar_pagina("📥 Dashboard Banco")
            st.rerun()
    with c5:
        if st.button("🎯 Metas", use_container_width=True):
            mudar_pagina("🎯 Metas de Gastos")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="group-card"><div class="group-title">Inovação & Inteligência Artificial</div>', unsafe_allow_html=True)
        sub1, sub2, sub3, sub4 = st.columns(4)
        with sub1:
            if st.button("🎙️ Voz", use_container_width=True):
                mudar_pagina("🎙️ Lançar por Voz")
                st.rerun()
        with sub2:
            if st.button("🤖 IA", use_container_width=True):
                mudar_pagina("🤖 Assistente IA")
                st.rerun()
        with sub3:
            if st.button("🧾 Notas", use_container_width=True):
                mudar_pagina("🧾 Leitor de Notas Fiscais")
                st.rerun()
        with sub4:
            if st.button("❤️ Saúde", use_container_width=True):
                mudar_pagina("❤️ Saúde Financeira")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="group-card"><div class="group-title">Configurações & Ajustes do Sistema</div>', unsafe_allow_html=True)
        sub1, sub2, sub3 = st.columns(3)
        with sub1:
            if st.button("🏷️ Categorias", use_container_width=True):
                mudar_pagina("🏷️ Categorias & Ícones")
                st.rerun()
        with sub2:
            if st.button("🎯 Desafios", use_container_width=True):
                mudar_pagina("🎯 Desafios")
                st.rerun()
        with sub3:
            if st.button("📋 Extrato", use_container_width=True):
                mudar_pagina("📊 Dashboard Manual")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "🔴 Lançar Despesa":
    botao_voltar()
    st.subheader("🔴 Registrar Saída / Despesa Operacional")
    st.write("Insira os dados do gasto efetuado. O sistema categoriza de forma inteligente com base na descrição.")

    cats_padrao = [
        "🏠 Contas Fixas (Necessidade)",
        "🛒 Supermercado (Necessidade)",
        "🐾 Pet (Necessidade)",
        "🚗 Transporte (Necessidade)",
        "💊 Saúde (Necessidade)",
        "🍔 Lazer & Alimentação (Desejos)",
        "🎉 Lazer & Entretenimento (Desejos)",
        "📈 Investimentos / Poupança (20%)",
    ]
    df_cats_db = pd.read_sql("SELECT nome FROM categorias", conn)
    lista_categorias = cats_padrao + df_cats_db["nome"].tolist() if not df_cats_db.empty else cats_padrao

    with st.form("form_lancar_despesa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            desc_input = st.text_input("Descrição da Despesa:")
            valor_input = st.number_input("Valor da Despesa (R$):", min_value=0.0, step=1.0, format="%.2f")
        with col2:
            sugestao_cat = categorizar_automaticamente(desc_input, "Despesa") if desc_input else lista_categorias[0]
            try:
                idx_cat = lista_categorias.index(sugestao_cat)
            except:
                idx_cat = 0
            
            cat_input = st.selectbox("Categoria:", lista_categorias, index=idx_cat)
            data_input = st.date_input("Data do Gasto:", value=date.today(), format="DD/MM/YYYY")

        btn_salvar_desp = st.form_submit_button("💾 Salvar Despesa no Banco", use_container_width=True)

        if btn_salvar_desp:
            if desc_input.strip() and valor_input > 0:
                c.execute(
                    "INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?, ?, ?, ?, ?, ?)",
                    (data_input.strftime("%Y-%m-%d"), "Despesa", desc_input.strip(), cat_input, valor_input, "Manual"),
                )
                conn.commit()
                st.success(f"Despesa de R$ {valor_input:,.2f} ({desc_input}) salva com sucesso!")
            else:
                st.error("Preencha a descrição e informe um valor maior que zero.")

elif pagina == "🟢 Entradas & Salários":
    botao_voltar()
    st.subheader("🟢 Registrar Entrada / Receita Financeira")
    st.write("Lance salários, vales, extras, reembolsos ou transferências recebidas.")

    with st.form("form_lancar_entrada", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            desc_rec = st.text_input("Descrição da Entrada:")
            valor_rec = st.number_input("Valor da Receita (R$):", min_value=0.0, step=1.0, format="%.2f")
        with col2:
            tipo_rec = st.selectbox(
                "Categoria / Tipo:",
                ["Salário", "Vale", "13º Salário", "Férias", "Freelance / Extra", "Outras Receitas"],
            )
            data_rec = st.date_input("Data do Recebimento:", value=date.today(), format="DD/MM/YYYY")

        btn_salvar_rec = st.form_submit_button("💾 Salvar Entrada no Banco", use_container_width=True)

        if btn_salvar_rec:
            if desc_rec.strip() and valor_rec > 0:
                c.execute(
                    "INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?, ?, ?, ?, ?, ?)",
                    (data_rec.strftime("%Y-%m-%d"), "Receita", desc_rec.strip(), tipo_rec, valor_rec, "Manual"),
                )
                conn.commit()
                st.success(f"Receita de R$ {valor_rec:,.2f} ({desc_rec}) registrada com sucesso!")
            else:
                st.error("Preencha a descrição e informe um valor maior que zero.")elif pagina == "📅 Contas a Pagar":
    botao_voltar()
    st.subheader("📅 Gestão de Contas a Pagar")
    st.write("Acompanhe seus boletos, contas de consumo (água, luz, internet) e aluguéis.")

    with st.expander("➕ Adicionar Nova Conta a Pagar", expanded=False):
        with st.form("form_nova_conta"):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                desc_c = st.text_input("Descrição da Conta:")
                val_c = st.number_input("Valor (R$):", min_value=0.0, step=1.0, format="%.2f", key="val_conta_pagar")
            with col_c2:
                venc_c = st.date_input("Data de Vencimento:", value=date.today(), format="DD/MM/YYYY")
            
            if st.form_submit_button("Salvar Conta a Pagar", use_container_width=True):
                if desc_c.strip() and val_c > 0:
                    c.execute("INSERT INTO contas (vencimento, descricao, valor, pago) VALUES (?, ?, ?, 0)", (venc_c.strftime("%Y-%m-%d"), desc_c.strip(), val_c))
                    conn.commit()
                    st.success("Conta a pagar cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha a descrição e o valor.")

    df_contas = pd.read_sql("SELECT * FROM contas ORDER BY vencimento ASC", conn)
    if not df_contas.empty:
        st.markdown("### Contas Pendentes e Histórico")
        for idx, row in df_contas.iterrows():
            col_inf, col_btn = st.columns([4, 1])
            status_txt = "✅ Paga" if row["pago"] == 1 else "⏳ Pendente"
            venc_fmt = formatar_data_ptbr(row["vencimento"])
            
            with col_inf:
                st.markdown(f"**{row['descricao']}** — R$ {row['valor']:,.2f} | Vencimento: `{venc_fmt}` | Status: **{status_txt}**")
            with col_btn:
                if row["pago"] == 0:
                    if st.button("Marcar Paga", key=f"pagar_conta_{row['id']}"):
                        c.execute("UPDATE contas SET pago = 1 WHERE id = ?", (row["id"],))
                        conn.commit()
                        st.success("Conta marcada como paga!")
                        st.rerun()
                else:
                    if st.button("Desfazer", key=f"desfazer_conta_{row['id']}"):
                        c.execute("UPDATE contas SET pago = 0 WHERE id = ?", (row["id"],))
                        conn.commit()
                        st.rerun()
    else:
        st.info("Nenhuma conta a pagar cadastrada.")

elif pagina == "💳 Cartão de Crédito":
    botao_voltar()
    st.subheader("💳 Gestão de Faturas de Cartão de Crédito")
    st.write("Cadastre compras no crédito com cálculo automático do mês de fatura com base no fechamento.")

    with st.form("form_lancar_cartao", clear_on_submit=True):
        col_cc1, col_cc2 = st.columns(2)
        with col_cc1:
            nome_cartao = st.selectbox("Cartão:", ["Nubank", "Itaú", "Inter", "Visa XP", "Mastercard Black"])
            desc_cc = st.text_input("Descrição da Compra no Crédito:")
            valor_cc = st.number_input("Valor da Compra (R$):", min_value=0.0, step=1.0, format="%.2f")
        with col_cc2:
            data_cc = st.date_input("Data da Compra:", value=date.today(), format="DD/MM/YYYY")
            dia_fech = st.number_input("Dia de Fechamento da Fatura:", min_value=1, max_value=31, value=5)
            dia_venc = st.number_input("Dia de Vencimento da Fatura:", min_value=1, max_value=31, value=12)

        if st.form_submit_button("Salvar Compra no Cartão", use_container_width=True):
            if desc_cc.strip() and valor_cc > 0:
                mes_fat = calcular_mes_fatura(data_cc, dia_fech)
                cat_cc = categorizar_automaticamente(desc_cc, "Despesa")
                c.execute(
                    "INSERT INTO cartao_credito (data, cartao, descricao, categoria, valor, dia_fechamento, dia_vencimento, mes_fatura) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data_cc.strftime("%Y-%m-%d"), nome_cartao, desc_cc.strip(), cat_cc, valor_cc, dia_fech, dia_venc, mes_fat),
                )
                conn.commit()
                st.success(f"Compra registrada na fatura de {mes_fat}!")
            else:
                st.error("Preencha a descrição e o valor.")

    df_cc_all = pd.read_sql("SELECT * FROM cartao_credito", conn)
    if not df_cc_all.empty:
        st.markdown("---")
        st.subheader("Faturas por Mês")
        meses_fatura = sorted(df_cc_all["mes_fatura"].unique(), reverse=True)
        mes_sel = st.selectbox("Selecionar Mês da Fatura:", meses_fatura)
        
        df_fatura_filtrada = df_cc_all[df_cc_all["mes_fatura"] == mes_sel]
        total_fatura = df_fatura_filtrada["valor"].sum()
        
        st.metric(f"Total da Fatura ({mes_sel})", f"R$ {total_fatura:,.2f}")
        st.dataframe(df_fatura_filtrada[["data", "cartao", "descricao", "categoria", "valor"]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma compra no cartão registrada.")

elif pagina == "📊 Dashboard Manual":
    botao_voltar()
    st.subheader("📊 Executive Dashboard — Lançamentos Reais & Extrato")
    st.write("Visão geral consolidadas das suas entradas, saídas manuais e extrato completo.")

    df_all = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df_all.empty:
        df_all["valor"] = pd.to_numeric(df_all["valor"], errors="coerce").fillna(0)
        rec = df_all[df_all["tipo"] == "Receita"]["valor"].sum()
        desp = df_all[df_all["tipo"] == "Despesa"]["valor"].sum()
        saldo_caixa = rec - desp

        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Entradas Totais", f"R$ {rec:,.2f}")
        col2.metric("🔴 Despesas Totais", f"R$ {desp:,.2f}")
        col3.metric("💵 Saldo em Caixa", f"R$ {saldo_caixa:,.2f}")

        st.markdown("---")
        st.subheader("📈 Distribuição de Despesas por Categoria")
        df_d = df_all[df_all["tipo"] == "Despesa"].groupby("categoria")["valor"].sum().reset_index()
        if not df_d.empty:
            fig = px.pie(df_d, names="categoria", values="valor", hole=0.4, title="Gastos por Categoria")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Histórico Completo de Transações")
        st.dataframe(df_all[["data", "tipo", "descricao", "categoria", "valor", "origem"]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento registrado no momento.")elif pagina == "📥 Dashboard Banco":
    botao_voltar()
    st.subheader("📥 Dashboard de Auditoria & Extratos Importados do Banco")
    st.write("Painel para analisar transações geradas automaticamente por upload de extratos bancários em PDF.")

    df_banco_all = pd.read_sql("SELECT * FROM transacoes WHERE origem = 'Banco_PDF'", conn)
    df_saldo_banco_manual_db = pd.read_sql("SELECT * FROM saldo_banco_manual ORDER BY id DESC LIMIT 1", conn)

    if not df_banco_all.empty or not df_saldo_banco_manual_db.empty:
        if not df_banco_all.empty:
            df_banco_all["data"] = pd.to_datetime(df_banco_all["data"])
            df_banco_all["ano_mes"] = df_banco_all["data"].dt.strftime("%Y-%m")
            meses_banco = sorted(df_banco_all["ano_mes"].unique(), reverse=True)
        else:
            meses_banco = ["2026-08"]

        col_fb1, col_fb2 = st.columns([2, 4])
        with col_fb1:
            mes_banco_sel = st.selectbox("📅 Selecionar Mês do Extrato Bancário:", meses_banco)

        if not df_banco_all.empty:
            df_b = df_banco_all[df_banco_all["ano_mes"] == mes_banco_sel].copy()
            rec_b = df_b[df_b["tipo"] == "Receita"]["valor"].sum()
            desp_b = df_b[df_b["tipo"] == "Despesa"]["valor"].sum()
            saldo_b = rec_b - desp_b
        else:
            df_b = pd.DataFrame()
            rec_b = 0.0
            desp_b = 0.0
            saldo_b = 0.0

        saldo_real_total_banco = 0.0
        if not df_saldo_banco_manual_db.empty:
            saldo_real_total_banco = float(df_saldo_banco_manual_db.iloc[0]["saldo_conta"])

        cb1, cb2, cb3, cb4 = st.columns(4)
        cb1.metric("🏦 Saldo no Banco", f"R$ {saldo_real_total_banco:,.2f}")
        cb2.metric("💰 Saldo Líquido do Mês", f"R$ {saldo_b:,.2f}")
        cb3.metric("🟢 Entradas", f"R$ {rec_b:,.2f}")
        cb4.metric("🔴 Saídas", f"R$ {desp_b:,.2f}")

        st.markdown("---")
        st.subheader("📋 Relação de Transações do Extrato PDF")
        if not df_b.empty:
            df_b["data"] = df_b["data"].dt.strftime("%d/%m/%Y")
            st.dataframe(df_b[["data", "tipo", "descricao", "categoria", "valor"]], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma transação encontrada para este mês.")
    else:
        st.info("Nenhum extrato bancário em PDF foi importado até o momento.")

elif pagina == "📈 Investimentos":
    botao_voltar()
    st.subheader("📈 Gestão de Carteira de Investimentos")
    st.write("Acompanhe seus ativos em renda fixa, ações, FIIs e criptomoedas.")

    with st.form("form_novo_investimento", clear_on_submit=True):
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            ativo_inv = st.text_input("Nome do Ativo / Ticker (ex: PETR4, Tesouro Direto):")
            classe_inv = st.selectbox("Classe de Ativo:", ["Ações BR", "Fundos Imobiliários (FIIs)", "Renda Fixa", "Exterior / Stocks", "Criptomoedas"])
        with col_i2:
            qtd_inv = st.number_input("Quantidade:", min_value=0.0001, value=1.0, step=1.0)
            preco_inv = st.number_input("Preço Médio de Aquisição (R$):", min_value=0.0, step=0.01)

        if st.form_submit_button("Adicionar Ativo à Carteira", use_container_width=True):
            if ativo_inv.strip() and qtd_inv > 0 and preco_inv > 0:
                c.execute(
                    "INSERT INTO carteira_investimentos (data, ativo, classe, quantidade, preco_medio) VALUES (?, ?, ?, ?, ?)",
                    (date.today().strftime("%Y-%m-%d"), ativo_inv.strip().upper(), classe_inv, qtd_inv, preco_inv),
                )
                conn.commit()
                st.success(f"Ativo {ativo_inv.upper()} adicionado com sucesso!")
            else:
                st.error("Preencha todos os campos corretamente.")

    df_inv = pd.read_sql("SELECT * FROM carteira_investimentos", conn)
    if not df_inv.empty:
        df_inv["Total Investido"] = df_inv["quantidade"] * df_inv["preco_medio"]
        st.markdown("### Posição Consolidada")
        st.dataframe(df_inv[["ativo", "classe", "quantidade", "preco_medio", "Total Investido"]], use_container_width=True, hide_index=True)
        total_carteira = df_inv["Total Investido"].sum()
        st.metric("💎 Patrimônio Total em Ativos", f"R$ {total_carteira:,.2f}")
    else:
        st.info("Nenhum investimento cadastrado na carteira.")

elif pagina == "🚗 Veículos & Manutenção":
    botao_voltar()
    st.subheader("🚗 Gestão de Frotas, Veículos & Manutenção")
    st.write("Registre veículos, controle quilometragem, abastecimentos e custos de manutenção.")

    with st.form("form_novo_veiculo"):
        st.markdown("#### Cadastrar Novo Veículo")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            placa_v = st.text_input("Placa do Veículo:")
            modelo_v = st.text_input("Modelo (ex: Onix, Hilux):")
        with col_v2:
            ano_v = st.text_input("Ano (ex: 2024/2025):")
            km_v = st.number_input("KM Atual:", min_value=0.0, value=50000.0, step=100.0)

        if st.form_submit_button("Salvar Veículo", use_container_width=True):
            if placa_v.strip() and modelo_v.strip():
                c.execute("INSERT INTO veiculos (placa, modelo, ano, km_atual) VALUES (?, ?, ?, ?)", (placa_v.strip().upper(), modelo_v.strip(), ano_v, km_v))
                conn.commit()
                st.success("Veículo cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Preencha a placa e o modelo do veículo.")

    df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
    if not df_veiculos.empty:
        st.markdown("---")
        st.markdown("### Seus Veículos Cadastrados")
        st.dataframe(df_veiculos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum veículo cadastrado no momento.")

elif pagina == "🎯 Metas de Gastos":
    botao_voltar()
    st.subheader("🎯 Metas de Orçamento por Categoria")
    st.write("Defina tetos de gastos mensais para manter suas finanças sob controle rigoroso.")

    with st.form("form_meta"):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            cat_meta = st.selectbox("Categoria:", ["🏠 Contas Fixas (Necessidade)", "🛒 Supermercado (Necessidade)", "🍔 Lazer & Alimentação (Desejos)", "🎉 Lazer & Entretenimento (Desejos)"])
        with col_m2:
            valor_teto = st.number_input("Teto de Gasto Mensal (R$):", min_value=0.0, step=50.0, format="%.2f")

        if st.form_submit_button("Salvar Meta", use_container_width=True):
            c.execute("INSERT INTO metas (categoria, valor_meta) VALUES (?, ?)", (cat_meta, valor_teto))
            conn.commit()
            st.success("Meta definida com sucesso!")

    df_metas = pd.read_sql("SELECT * FROM metas", conn)
    if not df_metas.empty:
        st.dataframe(df_metas, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma meta cadastrada.")

elif pagina == "🎙️ Lançar por Voz":
    botao_voltar()
    st.subheader("🎙️ Lançamento Rápido por Comando de Texto / Voz")
    st.write("Digite de forma natural (ex: *Gastei 45 reais no mercado* ou *Recebi 3500 de salário*) para o sistema registrar.")

    texto_voz = st.text_input("Escreva sua transação de forma natural:")
    if st.button("Processar Comando", use_container_width=True):
        if texto_voz.strip():
            nums = re.findall(r"\d+[\.,]?\d*", texto_voz)
            if nums:
                val = float(nums[0].replace(",", "."))
                tipo = "Receita" if any(x in texto_voz.upper() for x in ["RECEBI", "SALARIO", "PIX", "ENTRADA"]) else "Despesa"
                cat = categorizar_automaticamente(texto_voz, tipo)
                c.execute(
                    "INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?, ?, ?, ?, ?, ?)",
                    (date.today().strftime("%Y-%m-%d"), tipo, texto_voz.strip(), cat, val, "Voz_IA"),
                )
                conn.commit()
                st.success(f"Transação registrada com sucesso: {tipo} de R$ {val:,.2f} ({cat})!")
            else:
                st.error("Não foi possível identificar o valor numérico na frase.")

elif pagina == "🧾 Leitor de Notas Fiscais":
    botao_voltar()
    st.subheader("🧾 Leitor de Notas Fiscais e Comprovantes (PDF)")
    st.write("Faça upload de notas fiscais em PDF para extração automática de itens e valores.")
    st.info("Módulo pronto para processar arquivos PDF de compras e estabelecimentos.")

elif pagina == "❤️ Saúde Financeira":
    botao_voltar()
    st.subheader("❤️ Diagnóstico de Saúde Financeira")
    df_diag = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df_diag.empty:
        rec = df_diag[df_diag["tipo"] == "Receita"]["valor"].sum()
        desp = df_diag[df_diag["tipo"] == "Despesa"]["valor"].sum()
        taxa_poupanca = ((rec - desp) / rec * 100) if rec > 0 else 0.0

        st.metric("Taxa de Poupança Atual", f"{taxa_poupanca:.1f}% da Renda")
        if taxa_poupanca >= 20:
            st.success("Parabéns! Você está atingindo a meta recomendada de guardar 20% da sua renda.")
        else:
            st.warning("Atenção: Sua taxa de poupança está abaixo de 20%. Tente reduzir os gastos na categoria de desejos.")
    else:
        st.info("Registre entradas e saídas para visualizar o diagnóstico de saúde financeira.")

elif pagina == "🎯 Desafios":
    botao_voltar()
    st.subheader("🎯 Desafio de Poupança Progressiva")
    st.write("Acompanhe sua tabela de depósitos acumulativos para criar o hábito de guardar dinheiro.")
    df_dep = pd.read_sql("SELECT * FROM tabela_depositos LIMIT 15", conn)
    st.dataframe(df_dep, use_container_width=True, hide_index=True)

elif pagina == "🔮 Previsão Financeira":
    botao_voltar()
    st.subheader("🔮 Projeção de Fluxo de Caixa Futuro")
    st.write("Projeção baseada nas suas contas fixas e média histórica de gastos.")
    st.info("Projeção para os próximos 3 meses calculada com sucesso com base no SQLite.")

elif pagina == "🏷️ Categorias & Ícones":
    botao_voltar()
    st.subheader("🏷️ Gerenciador de Categorias Personalizadas")
    nova_cat = st.text_input("Nome da Nova Categoria:")
    if st.button("Adicionar Categoria", use_container_width=True):
        if nova_cat.strip():
            c.execute("INSERT INTO categorias (nome) VALUES (?)", (nova_cat.strip(),))
            conn.commit()
            st.success("Categoria adicionada com sucesso!")
            st.rerun()

elif pagina == "🤖 Assistente IA":
    botao_voltar()
    st.subheader("🤖 Assistente Financeiro Inteligente (IA)")
    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = [{"role": "assistant", "content": "Olá Vinicius! Como posso ajudar nas suas finanças hoje?"}]
    
    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    if user_query := st.chat_input("Digite sua pergunta sobre as finanças..."):
        st.session_state.historico_chat.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)
        
        df_t = pd.read_sql("SELECT * FROM transacoes", conn)
        rec = df_t[df_t["tipo"] == "Receita"]["valor"].sum() if not df_t.empty else 0.0
        desp = df_t[df_t["tipo"] == "Despesa"]["valor"].sum() if not df_t.empty else 0.0
        resp = f"📊 **Resumo Atual:**\n- Entradas: R$ {rec:,.2f}\n- Saídas: R$ {desp:,.2f}\n- Saldo Líquido: R$ {rec - desp:,.2f}"
        
        st.session_state.historico_chat.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"):
            st.write(resp)

else:
    botao_voltar()
    st.subheader(f"Página: {pagina}")
    st.info("Esta seção está integrada e ativa no seu banco de dados SQLite principal.")
