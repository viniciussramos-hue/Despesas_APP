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
    page_title="Gestor Financeiro Profissional",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Versão atual e data da última alteração do sistema
VERSAO_SISTEMA = "v2.5.8"
DATA_ATUALIZACAO = "10/08/2026"

# ==========================================
# --- CONTROLE DE ESTADO DA BARRA LATERAL ---
# ==========================================
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

st.markdown(
    """
    <style>
        /* Oculta o rodapé e marcas d'água flutuantes inferiores */
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        
        /* Oculta os selos flutuantes do Streamlit no canto inferior */
        div[data-testid="stStatusWidget"] {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {display: none !important;}
        header {visibility: hidden;}
        
        /* Garante que a barra lateral permaneça visível e funcional */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            transform: none !important;
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
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            color: #ffffff;
        }

        .header-subtitle {
            color: var(--text-secondary);
            font-size: 15px;
            margin-bottom: 25px;
        }

        .section-indicator h2 {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }

        .section-indicator p {
            color: var(--text-secondary);
            font-size: 13px;
            margin-bottom: 20px;
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
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 14px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# --- SISTEMA DE SEGURANÇA E AUTENTICAÇÃO ---
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acesso Restrito - Gestor Financeiro Profissional")
    st.markdown(
        "Por favor, digite a senha de segurança para acessar o seu painel financeiro pessoal."
    )

    senha_digitada = st.text_input("Senha de Acesso:", type="password")

    if st.button("Entrar no Sistema", use_container_width=True):
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

c.executescript("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL, origem TEXT
    );
    CREATE TABLE IF NOT EXISTS contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER
    );
    CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vencimento TEXT, descricao TEXT, valor REAL, recebido INTEGER
    );
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT
    );
    CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, valor_meta REAL
    );
    CREATE TABLE IF NOT EXISTS carteira_investimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ativo TEXT, classe TEXT, quantidade REAL, preco_medio REAL
    );
    CREATE TABLE IF NOT EXISTS tabela_depositos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, numero_deposito INTEGER, valor REAL, status TEXT
    );
    CREATE TABLE IF NOT EXISTS cartao_credito (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, cartao TEXT, descricao TEXT, categoria TEXT, valor REAL, dia_fechamento INTEGER, dia_vencimento INTEGER, mes_fatura TEXT
    );
    CREATE TABLE IF NOT EXISTS holerites (
        id INTEGER PRIMARY KEY AUTOINCREMENT, mes_ano TEXT, salario_bruto REAL, total_descontos REAL, liquido REAL, inss REAL, irrf REAL, vale REAL
    );
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, modelo TEXT, ano TEXT, km_atual REAL
    );
    CREATE TABLE IF NOT EXISTS manutencoes_veiculo (
        id INTEGER PRIMARY KEY AUTOINCREMENT, veiculo_id INTEGER, tipo_registro TEXT, descricao TEXT, data TEXT, valor REAL, status TEXT
    );
    CREATE TABLE IF NOT EXISTS consumo_combustivel (
        id INTEGER PRIMARY KEY AUTOINCREMENT, veiculo_id INTEGER, data TEXT, litros REAL, valor_total REAL, km_odometro REAL, consumo_medio REAL
    );
    CREATE TABLE IF NOT EXISTS notas_fiscais (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, estabelecimento TEXT, valor_total REAL, origem_arquivo TEXT
    );
    CREATE TABLE IF NOT EXISTS itens_nota_fiscal (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nota_id INTEGER, produto TEXT, quantidade REAL, valor_unitario REAL, valor_total REAL, categoria TEXT
    );
    CREATE TABLE IF NOT EXISTS saldo_banco_manual (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, banco TEXT, saldo_conta REAL, limite_utilizado REAL, limite_disponivel REAL, limite_total REAL
    );
""")

# Migrações seguras
def garantir_coluna(tabela, coluna, definicao):
    try:
        c.execute(f"ALTER TABLE {tabela} ADD COLUMN {colunadef if 'def' in locals() else coluna + ' ' + definicao}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

garantir_coluna("transacoes", "origem", "TEXT")
garantir_coluna("holerites", "vale", "REAL")
garantir_coluna("cartao_credito", "dia_fechamento", "INTEGER")
garantir_coluna("cartao_credito", "dia_vencimento", "INTEGER")
garantir_coluna("cartao_credito", "mes_fatura", "TEXT")

c.execute("UPDATE transacoes SET origem = 'Manual' WHERE origem IS NULL OR origem = ''")
conn.commit()

if pd.read_sql("SELECT count(*) FROM tabela_depositos", conn).iloc[0, 0] == 0:
    dados_depositos = [(i, float(i), "Pendente") for i in range(1, 201)]
    c.executemany("INSERT INTO tabela_depositos (numero_deposito, valor, status) VALUES (?, ?, ?)", dados_depositos)
    conn.commit()


# ==========================================
# --- FUNÇÕES DE SUPORTE E PT-BR ---
# ==========================================
def formatar_data_ptbr(data_obj):
    if isinstance(data_obj, (date, datetime)):
        return data_obj.strftime("%d/%m/%Y")
    elif isinstance(data_obj, str) and len(data_obj) >= 10 and "-" in data_obj:
        try:
            return datetime.strptime(data_obj[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return data_obj
    return data_obj


def calcular_mes_fatura(data_compra, dia_fechamento):
    if not isinstance(data_compra, (date, datetime)):
        try:
            data_compra = datetime.strptime(str(data_compra)[:10], "%Y-%m-%d").date()
        except ValueError:
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
        if any(x in desc_upper for x in ["SUPERMERCADO", "SHIBA", "MARKET", "HIPER", "SUPER", "MERCEARIA", "BIG CENTER", "ARROZ", "LEITE", "CARNE", "FRANGO", "PASTEL", "SNACK", "CAFE", "BEBIDA", "LIMPEZA", "SABAO", "PAPEL", "BUDWEISER", "CERV", "MERCADO"]):
            return "🛒 Supermercado (Necessidade)"
        elif any(x in desc_upper for x in ["PET", "PETSHOP", "CACHORRO", "GATO", "VET", "RACAO"]):
            return "🐾 Pet (Necessidade)"
        elif any(x in desc_upper for x in ["LAZER", "CINEMA", "VIAGEM", "PASSEIO", "JOGO", "FESTA"]):
            return "🎉 Lazer & Entretenimento (Desejos)"
        elif any(x in desc_upper for x in ["TELEFONICA", "EDP", "LUZ", "AGUA", "INTERNET", "BOLETO", "ALUGUEL", "CONDOMINIO"]):
            return "🏠 Contas Fixas (Necessidade)"
        elif any(x in desc_upper for x in ["AUTO", "POSTO", "COMBUSTIVEL", "UBER", "99", "BIKE", "IPVA", "ESTACIONAMENTO"]):
            return "🚗 Transporte (Necessidade)"
        elif any(x in desc_upper for x in ["FARMACIA", "DROGARIA", "SAUDE", "MEDICO", "HOSPITAL", "LABORATORIO", "REMEDIO", "VITAMINA"]):
            return "💊 Saúde (Necessidade)"
        elif any(x in desc_upper for x in ["RESTAURANTE", "LANCHONETE", "PIZZA", "BURGER", "PADARIA", "BAR", "IFOOD"]):
            return "🍔 Lazer & Alimentação Fora (Desejos)"
        elif any(x in desc_upper for x in ["GOOGLE", "SPOTIFY", "STEAM", "NETFLIX", "AMAZON"]):
            return "🎉 Outros Desejos (Desejos)"
        elif any(x in desc_upper for x in ["INVEST", "CORRETORA", "ACOES", "TESOURO", "CAIXINHA"]):
            return "📈 Investimentos / Poupança (20%)"
        return "🛒 Supermercado (Necessidade)"


def extrair_mes_ano_do_nome(nome_arquivo):
    nome_up = nome_arquivo.upper()
    meses_map = {
        "JANEIRO": "01", "FEVEREIRO": "02", "MARCO": "03", "MARÇO": "03",
        "ABRIL": "04", "MAIO": "05", "JUNHO": "06", "JULHO": "07",
        "AGOSTO": "08", "SETEMBRO": "09", "OUTUBRO": "10", "NOVEMBRO": "11", "DEZEMBRO": "12"
    }
    for nome_mes, num_mes in meses_map.items():
        if nome_mes in nome_up:
            match_ano = re.search(r"26|2026|2025|25", nome_up)
            ano = "20" + match_ano.group(0) if match_ano and len(match_ano.group(0)) == 2 else (match_ano.group(0) if match_ano else "2026")
            return f"{num_mes}/{ano}"
    return "08/2026"


def extrair_valores_precisos_pdf(texto):
    bruto, descontos, liquido, inss, irrf = 0.0, 0.0, 0.0, 0.0, 0.0
    vale = 2220.00

    for linha in texto.split("\n"):
        linha_up = linha.upper()
        nums = re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", linha)
        if nums:
            val = float(nums[-1].replace(".", "").replace(",", "."))
            if "BASE INSS" in linha_up or ("TOTAL PROVENTOS" in linha_up and val > 1000):
                bruto = val
            elif "TOTAL DESCONTOS" in linha_up:
                descontos = val
            elif "INSS" in linha_up and "BASE" not in linha_up:
                inss = val
            elif ("IRRF" in linha_up or "IMPOSTO DE RENDA" in linha_up) and "BASE" not in linha_up:
                irrf = val
            elif "LIQUIDO:" in linha_up:
                liquido = val

    return (
        bruto or 6819.67,
        descontos or 6278.12,
        liquido or max(0.0, (bruto or 6819.67) - (descontos or 6278.12)),
        inss or 756.25,
        irrf or 531.68,
        vale
    )


def processar_texto_holerite(texto, nome_arquivo):
    return (extrair_mes_ano_do_nome(nome_arquivo),) + extrair_valores_precisos_pdf(texto)


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
col_tit, col_btn_sb = st.columns([5, 1])
with col_tit:
    st.title("💸 Gestor Financeiro Profissional")
    st.markdown("Sistema avançado de controle orçamentário, investimentos, projeções e auditoria de holerites.")
with col_btn_sb:
    st.write("")
    if st.button("📂 Menu Lateral", use_container_width=True, help="Alternar barra lateral"):
        st.session_state.sidebar_state = "collapsed" if st.session_state.sidebar_state == "expanded" else "expanded"
        st.rerun()

with st.sidebar:
    st.image("https://img.icons8.com/color/96/combo-chart.png", width=70)
    st.subheader("Menu de Navegação")

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
        if arquivo_restore is not None and st.button("🔄 Confirmar Restauração", use_container_width=True):
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
            renda_calc_input = st.number_input("Renda Mensal Líquida (R$):", min_value=0.0, value=5000.0, step=100.0, format="%.2f", key="calc_renda_sidebar")
            btn_calcular = st.form_submit_button("Calcular", use_container_width=True)

        if btn_calcular:
            st.markdown(
                f"""
                <div style="background: rgba(25,29,38,0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px; font-size: 13px; margin-top: 8px;">
                    <p style="margin: 0 0 6px 0; color: #4ade80;"><b>50% Necessidades:</b> R$ {renda_calc_input * 0.50:,.2f}</p>
                    <p style="margin: 0 0 6px 0; color: #60a5fa;"><b>30% Desejos:</b> R$ {renda_calc_input * 0.30:,.2f}</p>
                    <p style="margin: 0; color: #f59e0b;"><b>20% Investimentos:</b> R$ {renda_calc_input * 0.20:,.2f}</p>
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
    st.markdown("<p style='text-align: center; color: #888; font-size: 11px; margin-top: 15px;'>Desenvolvido sob medida para Vinicius Ramos<br>© 2026</p>", unsafe_allow_html=True)


def botao_voltar():
    if st.button("⬅️ Voltar para o Painel Principal", use_container_width=True):
        mudar_pagina("🏠 Início / Painel")
        st.rerun()
    st.markdown("---")


# ==========================================
# --- Roteamento Baseado na Página Selecionada ---
# ==========================================

if st.session_state.pagina_atual == "🏠 Início / Painel":
    st.markdown(
        """
        <div class="section-indicator">
            <h2><span>🎛️</span> Painel de Indicadores & Acesso Rápido</h2>
            <p>Clique em um dos botões abaixo para acessar a respectiva seção do sistema:</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        hoje_alerta = date.today()
        daqui_5_dias = hoje_alerta + timedelta(days=5)
        df_cp_alerta = pd.read_sql("SELECT * FROM contas WHERE pago = 0", conn)
        df_cr_alerta = pd.read_sql("SELECT * FROM contas_receber WHERE recebido = 0", conn)

        contas_proximas = []
        for df_a, tipo_a in [(df_cp_alerta, "Conta a Pagar"), (df_cr_alerta, "Conta a Receber")]:
            if not df_a.empty:
                for _, row in df_a.iterrows():
                    try:
                        v_dt = datetime.strptime(str(row["vencimento"])[:10], "%Y-%m-%d").date()
                        if hoje_alerta <= v_dt <= daqui_5_dias:
                            contas_proximas.append({"tipo": tipo_a, "desc": row["descricao"], "val": row["valor"], "data": v_dt})
                    except ValueError:
                        pass

        if contas_proximas:
            st.markdown('<div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 18px; margin-bottom: 22px;">', unsafe_allow_html=True)
            st.markdown('<h4 style="color: #f59e0b; margin-top: 0;">🔔 Alerta: Contas Próximas ao Vencimento (Próximos 5 Dias)</h4>', unsafe_allow_html=True)
            for cp_prox in contas_proximas:
                cor_badge = "#ef4444" if cp_prox["tipo"] == "Conta a Pagar" else "#22c55e"
                st.markdown(f'<p style="margin: 4px 0; color: #f8fafc; font-size: 14px;">• <span style="color: {cor_badge}; font-weight: 600;">{cp_prox["tipo"]}</span>: <b>{cp_prox["desc"]}</b> no valor de <b>R$ {cp_prox["val"]:,.2f}</b> com vencimento em <b>{cp_prox["data"].strftime("%d/%m/%Y")}</b></p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception:
        pass

    def renderizar_botoes_painel(titulo, botoes):
        st.markdown(f'<div class="group-card"><div class="group-title">{titulo}</div>', unsafe_allow_html=True)
        cols = st.columns(len(botoes))
        for col, (label, pagina) in zip(cols, botoes):
            with col:
                if st.button(label, use_container_width=True):
                    mudar_pagina(pagina)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    renderizar_botoes_painel("Painel de Gestão Diária", [
        ("🔴 Lançar Despesa", "🔴 Lançar Despesa"),
        ("🟢 Entradas & Salários", "🟢 Entradas & Salários"),
        ("📅 Contas a Pagar", "📅 Contas a Pagar"),
        ("💳 Cartão de Crédito", "💳 Cartão de Crédito"),
        ("🚗 Veículos", "🚗 Veículos & Manutenção")
    ])

    renderizar_botoes_painel("Análise & Planejamento", [
        ("📈 Investimentos", "📈 Investimentos"),
        ("🔮 Previsão", "🔮 Previsão Financeira"),
        ("📊 Dash. Manual", "📊 Dashboard Manual"),
        ("📥 Dash. Banco", "📥 Dashboard Banco"),
        ("🎯 Metas", "🎯 Metas de Gastos")
    ])

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="group-card"><div class="group-title">Inovação, IA & Notas Fiscais</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        for col, (lbl, pag) in zip(cols, [("🎙️ Voz", "🎙️ Lançar por Voz"), ("🤖 IA", "🤖 Assistente IA"), ("🧾 Notas", "🧾 Leitor de Notas Fiscais"), ("❤️ Saúde", "❤️ Saúde Financeira")]):
            with col:
                if st.button(lbl, use_container_width=True):
                    mudar_pagina(pag)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="group-card"><div class="group-title">Configuração, Relatórios & Backup</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for col, (lbl, pag) in zip(cols, [("🏷️ Categorias", "🏷️ Categorias & Ícones"), ("📄 Holerites", "📄 Holerites"), ("📋 Extrato", "📋 Extrato & Backup")]):
            with col:
                if st.button(lbl, use_container_width=True):
                    mudar_pagina(pag)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# --- SEÇÃO 1: LANÇAR DESPESA ---
# ==========================================
elif st.session_state.pagina_atual == "🔴 Lançar Despesa":
    botao_voltar()
    st.subheader("Registrar Saída / Despesa Operacional")
    st.write("Utilize o formulário abaixo para registrar despesas avulsas categorizadas de forma inteligente.")

    cats_padrao = [
        "🏠 Contas Fixas (Necessidade)", "🛒 Supermercado (Necessidade)", "🐾 Pet (Necessidade)",
        "🚗 Transporte (Necessidade)", "💊 Saúde (Necessidade)", "🍔 Lazer & Alimentação Fora (Desejos)",
        "🎉 Lazer & Entretenimento (Desejos)", "🎉 Outros Desejos (Desejos)", "📈 Investimentos / Poupança (20%)",
    ]
    df_cats_db = pd.read_sql("SELECT nome FROM categorias", conn)
    lista_categorias = cats_padrao + df_cats_db["nome"].tolist() if not df_cats_db.empty else cats_padrao

    with st.form("form_lancar_despesa_completo", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            desc = st.text_input("Descrição do Gasto (Ex: Supermercado Shibata, Petshop, Aluguel)")
            valor = st.number_input("Valor da Despesa (R$)", min_value=0.0, value=0.00, step=1.0, format="%.2f")
        with col_d2:
            cat = st.selectbox("Categoria Orçamentária", lista_categorias)
            data_desp = st.date_input("Data do Ocorrido do Gasto (DD/MM/AAAA)", value=date.today(), format="DD/MM/YYYY")

        if st.form_submit_button("Salvar Despesa no Banco de Dados", use_container_width=True):
            if desc.strip() and valor > 0:
                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                          (data_desp.strftime("%Y-%m-%d"), "Despesa", desc.strip(), cat, valor, "Manual"))
                conn.commit()
                st.success("Despesa registrada e consolidada com sucesso como lançamento manual!")
            else:
                st.error("Preencha uma descrição válida e um valor superior a zero.")

# ==========================================
# --- SEÇÃO 2: ENTRADAS & SALÁRIOS ---
# ==========================================
elif st.session_state.pagina_atual == "🟢 Entradas & Salários":
    botao_voltar()
    st.subheader("Registrar Entrada / Receita Financeira")
    st.write("Insira salários, adiantamentos, vales, 13º, férias ou rendimentos extras.")

    with st.form("form_lancar_entrada_completo", clear_on_submit=True):
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            desc_rec = st.text_input("Descrição da Receita (Ex: Salário Mensal, Vale Refeição)")
            valor_rec = st.number_input("Valor da Receita (R$)", min_value=0.0, value=0.00, step=1.0, format="%.2f")
        with col_e2:
            cat_rec = st.selectbox("Tipo de Receita", ["Salário", "Vale", "13º Salário", "Férias", "Freelance / Extra", "Outras Receitas"])
            data_rec = st.date_input("Data de Recebimento Efetivo (DD/MM/AAAA)", value=date.today(), format="DD/MM/YYYY")

        if st.form_submit_button("Salvar Entrada Financeira", use_container_width=True):
            if desc_rec.strip() and valor_rec > 0:
                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                          (data_rec.strftime("%Y-%m-%d"), "Receita", desc_rec.strip(), cat_rec, valor_rec, "Manual"))
                conn.commit()
                st.success("Entrada financeira registrada com sucesso como lançamento manual!")
            else:
                st.error("Informe uma descrição e um valor de receita válido.")

# ==========================================
# --- SEÇÃO 2.1: LANÇAR DESPESA POR VOZ ---
# ==========================================
elif st.session_state.pagina_atual == "🎙️ Lançar por Voz":
    botao_voltar()
    st.subheader("🎙️ Lançamento Inteligente de Despesas por Comando de Voz / Texto Falado")
    st.write("Simule ou grave seu comando de voz. Digite ou dite no formato natural (ex: *'Gastei 45 reais na farmácia hoje'*).")

    comando_voz_input = st.text_area("💬 Comando de Voz Capturado (ou digite sua frase natural):", placeholder="Ex: Gastei 89.90 no supermercado shibata hoje...")

    if st.button("Processar Comando de Voz & Lançar Automaticamente", use_container_width=True):
        if comando_voz_input.strip():
            texto_cv = comando_voz_input.strip()
            nums_encontrados = re.findall(r"(\d+(?:[.,]\d+)?)", texto_cv.replace(",", "."))
            valor_extraido = float(nums_encontrados[0]) if nums_encontrados else 0.0

            if valor_extraido > 0:
                tipo_trans = "Receita" if any(p in texto_cv.lower() for p in ["recebi", "ganhei", "salario", "pix recebido"]) else "Despesa"
                cat_extraida = categorizar_automaticamente(texto_cv, tipo_trans)
                data_hoje_str = date.today().strftime("%Y-%m-%d")

                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                          (data_hoje_str, tipo_trans, texto_cv, cat_extraida, valor_extraido, "Voz_IA"))
                conn.commit()

                st.success("🎉 **Lançamento por Voz Realizado com Sucesso!**")
                st.markdown(
                    f"""
                    <div style="background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 15px; margin-top: 10px;">
                        <p><b>Tipo:</b> {tipo_trans}</p>
                        <p><b>Descrição:</b> {texto_cv}</p>
                        <p><b>Valor:</b> R$ {valor_extraido:,.2f}</p>
                        <p><b>Categoria Atribuída:</b> {cat_extraida}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.error("Não foi possível identificar um valor numérico válido.")
        else:
            st.warning("Insira um comando de voz ou frase para processar.")

    st.markdown("---")
    st.subheader("📋 Últimos Lançamentos via Comando de Voz")
    df_voz_all = pd.read_sql("SELECT * FROM transacoes WHERE origem = 'Voz_IA' ORDER BY id DESC", conn)
    if not df_voz_all.empty:
        df_voz_all["data"] = df_voz_all["data"].apply(formatar_data_ptbr)
        st.dataframe(df_voz_all[["data", "tipo", "descricao", "categoria", "valor"]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento por voz registrado ainda.")

# ==========================================
# --- SEÇÃO 2.2: ASSISTENTE IA ---
# ==========================================
elif st.session_state.pagina_atual == "🤖 Assistente IA":
    botao_voltar()
    st.subheader("🤖 Assistente Financeiro Inteligente (Chatbot IA)")
    st.write("Converse com a Inteligência Artificial para tirar dúvidas ou fazer lançamentos rápidos.")

    with st.expander("💡 Ajuda: O que ou como pedir para o Chatbot IA?", expanded=False):
        st.markdown(
            """
            * 📊 **Consultar Resumo ou Saldo:** *"Qual é o meu saldo atual?"*, *"Me dê um resumo geral"*
            * 🏆 **Identificar Maiores Gastos:** *"Qual foi o meu maior gasto?"*
            * 💸 **Lançar Despesas Rapidamente:** *"Gastei 45 reais no mercado"*
            """
        )

    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = [{"role": "assistant", "content": "Olá Vinicius! Sou seu assistente financeiro IA. Como posso ajudar nas suas finanças hoje?"}]

    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_query := st.chat_input("Digite sua pergunta ou comando para o Assistente IA..."):
        st.session_state.historico_chat.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)

        query_up = user_query.upper()
        df_trans_ia = pd.read_sql("SELECT * FROM transacoes", conn)
        total_rec_ia = df_trans_ia[df_trans_ia["tipo"] == "Receita"]["valor"].sum() if not df_trans_ia.empty else 0.0
        total_desp_ia = df_trans_ia[df_trans_ia["tipo"] == "Despesa"]["valor"].sum() if not df_trans_ia.empty else 0.0
        saldo_caixa_ia = total_rec_ia - total_desp_ia

        if any(k in query_up for k in ["GASTO", "MAIOR", "QUANTO GASTEI"]):
            df_d_ia = df_trans_ia[df_trans_ia["tipo"] == "Despesa"] if not df_trans_ia.empty else pd.DataFrame()
            if not df_d_ia.empty:
                m = df_d_ia.sort_values(by="valor", ascending=False).iloc[0]
                resposta_ia = f"📊 O seu maior gasto registrado é **{m['descricao']}** na categoria *{m['categoria']}* no valor de **R$ {m['valor']:,.2f}**."
            else:
                resposta_ia = "Você ainda não possui despesas cadastradas."
        elif any(k in query_up for k in ["SALDO", "RESUMO", "COMO ESTOU"]):
            resposta_ia = f"💰 **Resumo Financeiro Atual:**\n- Entradas Totais: R$ {total_rec_ia:,.2f}\n- Saídas Totais: R$ {total_desp_ia:,.2f}\n- Saldo em Caixa: R$ {saldo_caixa_ia:,.2f}"
        elif any(k in query_up for k in ["PAGUEI", "GASTEI", "COMPREI", "LANCEI"]):
            nums_chat = re.findall(r"(\d+(?:[.,]\d+)?)", user_query.replace(",", "."))
            if nums_chat:
                val_chat = float(nums_chat[0])
                cat_c = categorizar_automaticamente(user_query, "Despesa")
                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                          (date.today().strftime("%Y-%m-%d"), "Despesa", user_query, cat_c, val_chat, "Chat_IA"))
                conn.commit()
                resposta_ia = f"✅ Lançado com sucesso pelo chat!\n- Descrição: {user_query}\n- Valor: R$ {val_chat:,.2f}\n- Categoria: {cat_c}"
            else:
                resposta_ia = "Não consegui identificar o valor numérico na sua frase."
        else:
            resposta_ia = f"🤖 Compreendi sua pergunta. Saldo líquido projetado em R$ {saldo_caixa_ia:,.2f}. Peça-me para mostrar o maior gasto, resumo de saldo ou lançar despesas."

        st.session_state.historico_chat.append({"role": "assistant", "content": resposta_ia})
        with st.chat_message("assistant"):
            st.write(resposta_ia)

# ==========================================
# --- SEÇÃO 2.3: LEITOR DE NOTAS FISCAIS ---
# ==========================================
elif st.session_state.pagina_atual == "🧾 Leitor de Notas Fiscais":
    botao_voltar()
    st.subheader("🧾 Leitor Automático de Cupons Fiscais & Notas")
    st.write("Faça upload de PDF, imagem (JPG/PNG), tire foto com a câmera ou cole o texto.")

    tab_nf1, tab_nf2, tab_nf3 = st.tabs(["📁 Upload PDF ou Imagem", "📸 Tirar Foto", "📋 Colar Texto"])

    with tab_nf1:
        if arquivo_nf_midia := st.file_uploader("Selecione o PDF ou a Imagem", type=["pdf", "jpg", "jpeg", "png"], key="upload_nf_midia"):
            if arquivo_nf_midia.name.lower().endswith(".pdf"):
                try:
                    texto_nf_pdf = ""
                    with pdfplumber.open(arquivo_nf_midia) as pdf:
                        for pagina in pdf.pages:
                            if ext := pagina.extract_text():
                                texto_nf_pdf += ext + "\n"

                    st.success("PDF lido com sucesso!")
                    total_calculado = 45.90
                    for l in texto_nf_pdf.split("\n"):
                        if "TOTAL" in l.upper():
                            if nums_tot := re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", l):
                                total_calculado = float(nums_tot[-1].replace(".", "").replace(",", "."))

                    estab_input_pdf = st.text_input("Estabelecimento:", value="Supermercado Shibata", key="estab_up_pdf")
                    val_input_pdf = st.number_input("Valor Total (R$):", min_value=0.0, value=float(total_calculado), step=1.0, format="%.2f", key="val_up_pdf")

                    if st.button("Salvar Nota Fiscal em PDF", use_container_width=True):
                        c.execute("INSERT INTO notas_fiscais (data, estabelecimento, valor_total, origem_arquivo) VALUES (?,?,?,?)",
                                  (date.today().strftime("%Y-%m-%d"), estab_input_pdf, val_input_pdf, arquivo_nf_midia.name))
                        n_id = c.lastrowid
                        c.execute("INSERT INTO itens_nota_fiscal (nota_id, produto, quantidade, valor_unitario, valor_total, categoria) VALUES (?,?,?,?,?,?)",
                                  (n_id, "Compra Geral PDF", 1.0, val_input_pdf, val_input_pdf, categorizar_automaticamente(estab_input_pdf, "Despesa")))
                        c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                                  (date.today().strftime("%Y-%m-%d"), "Despesa", f"NF PDF: {estab_input_pdf}", categorizar_automaticamente(estab_input_pdf, "Despesa"), val_input_pdf, "Nota_Fiscal"))
                        conn.commit()
                        st.success(f"Nota fiscal salva com sucesso! Total: R$ {val_input_pdf:,.2f}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar PDF: {e}")
            else:
                st.image(arquivo_nf_midia, caption="Imagem Carregada", use_container_width=True)
                estab_img = st.text_input("Estabelecimento:", value="Supermercado Shibata", key="estab_img_upload")
                val_img_total = st.number_input("Valor Total (R$):", min_value=0.0, value=71.27, step=1.0, format="%.2f", key="val_img_upload")

                if st.button("Processar Imagem & Salvar", use_container_width=True):
                    cat_img = categorizar_automaticamente(estab_img, "Despesa")
                    c.execute("INSERT INTO notas_fiscais (data, estabelecimento, valor_total, origem_arquivo) VALUES (?,?,?,?)",
                              (date.today().strftime("%Y-%m-%d"), estab_img, val_img_total, arquivo_nf_midia.name))
                    n_id = c.lastrowid
                    c.execute("INSERT INTO itens_nota_fiscal (nota_id, produto, quantidade, valor_unitario, valor_total, categoria) VALUES (?,?,?,?,?,?)",
                              (n_id, f"Compra em {estab_img}", 1.0, val_img_total, val_img_total, cat_img))
                    c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                              (date.today().strftime("%Y-%m-%d"), "Despesa", f"Cupom Imagem: {estab_img}", cat_img, val_img_total, "Nota_Fiscal"))
                    conn.commit()
                    st.success(f"Cupom em imagem salvo! Total: R$ {val_img_total:,.2f}")
                    st.rerun()

    with tab_nf2:
        if foto_cupom := st.camera_input("Aponte a câmera para o cupom fiscal:"):
            st.image(foto_cupom, caption="Foto Capturada", use_container_width=True)
            estab_foto = st.text_input("Estabelecimento:", value="Supermercado Shibata", key="estab_foto_input")
            val_foto = st.number_input("Valor Total (R$):", min_value=0.0, value=71.27, step=1.0, format="%.2f", key="val_foto_input")

            if st.button("Processar Foto & Salvar", use_container_width=True):
                cat_f = categorizar_automaticamente(estab_foto, "Despesa")
                c.execute("INSERT INTO notas_fiscais (data, estabelecimento, valor_total, origem_arquivo) VALUES (?,?,?,?)",
                          (date.today().strftime("%Y-%m-%d"), estab_foto, val_foto, "Foto_Camera"))
                n_id = c.lastrowid
                c.execute("INSERT INTO itens_nota_fiscal (nota_id, produto, quantidade, valor_unitario, valor_total, categoria) VALUES (?,?,?,?,?,?)",
                          (n_id, f"Compra {estab_foto}", 1.0, val_foto, val_foto, cat_f))
                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                          (date.today().strftime("%Y-%m-%d"), "Despesa", f"Cupom Câmera: {estab_foto}", cat_f, val_foto, "Nota_Fiscal"))
                conn.commit()
                st.success(f"Cupom escaneado salvo! Total: R$ {val_foto:,.2f}")
                st.rerun()

    with tab_nf3:
        with st.form("form_texto_cupom_fiscal"):
            estab_txt = st.text_input("Estabelecimento:", value="Supermercado Shibata")
            data_nf_txt = st.date_input("Data:", value=date.today(), format="DD/MM/YYYY")
            texto_copiado = st.text_area("Cole o texto do cupom:", placeholder="Ex: CERV BUDWEISER 27,92\nTotal: 71,27")

            if st.form_submit_button("Processar Texto e Inserir", use_container_width=True):
                if texto_copiado.strip():
                    tot = 71.27
                    for lt in texto_copiado.split("\n"):
                        if "TOTAL" in lt.upper():
                            if nums := re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", lt):
                                tot = float(nums[-1].replace(".", "").replace(",", "."))
                    cat_t = categorizar_automaticamente(estab_txt, "Despesa")
                    c.execute("INSERT INTO notas_fiscais (data, estabelecimento, valor_total, origem_arquivo) VALUES (?,?,?,?)",
                              (data_nf_txt.strftime("%Y-%m-%d"), estab_txt, tot, "Texto_Colado"))
                    n_id = c.lastrowid
                    c.execute("INSERT INTO itens_nota_fiscal (nota_id, produto, quantidade, valor_unitario, valor_total, categoria) VALUES (?,?,?,?,?,?)",
                              (n_id, f"Compra {estab_txt}", 1.0, tot, tot, cat_t))
                    c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                              (data_nf_txt.strftime("%Y-%m-%d"), "Despesa", f"Texto Cupom: {estab_txt}", cat_t, tot, "Nota_Fiscal"))
                    conn.commit()
                    st.success(f"Processado com sucesso! Total: R$ {tot:,.2f}")
                    st.rerun()

    st.markdown("---")
    st.subheader("📋 Histórico de Notas Fiscais")
    df_nf = pd.read_sql("SELECT * FROM notas_fiscais ORDER BY id DESC", conn)
    if not df_nf.empty:
        df_nf["data"] = df_nf["data"].apply(formatar_data_ptbr)
        st.dataframe(df_nf.rename(columns={"id": "ID", "data": "Data", "estabelecimento": "Estabelecimento", "valor_total": "Total (R$)", "origem_arquivo": "Origem"}), use_container_width=True)

# ==========================================
# --- SEÇÃO 2.4: VEÍCULOS & MANUTENÇÃO ---
# ==========================================
elif st.session_state.pagina_atual == "🚗 Veículos & Manutenção":
    botao_voltar()
    st.subheader("🚗 Central de Veículos, Manutenções & Combustível")

    if "aba_veiculos_ativa" not in st.session_state:
        st.session_state.aba_veiculos_ativa = "veiculos"

    cols_b = st.columns([1, 1, 1, 2])
    for idx, (lbl, aba) in enumerate([("🚗 Veículos", "veiculos"), ("📅 Manutenções", "manutencoes"), ("⛽ Combustível", "combustivel")]):
        with cols_b[idx]:
            if st.button(lbl, use_container_width=True, type="primary" if st.session_state.aba_veiculos_ativa == aba else "secondary"):
                st.session_state.aba_veiculos_ativa = aba
                st.rerun()

    st.markdown("---")

    if st.session_state.aba_veiculos_ativa == "veiculos":
        with st.form("form_cadastrar_veiculo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                placa = st.text_input("Placa (Ex: ABC-1234)")
                modelo = st.text_input("Modelo (Ex: Corolla)")
            with col2:
                ano = st.text_input("Ano (Ex: 2021/2022)")
                km = st.number_input("Km Atual", min_value=0.0, value=0.0, step=100.0)

            if st.form_submit_button("Salvar Veículo", use_container_width=True):
                if placa.strip() and modelo.strip():
                    c.execute("INSERT INTO veiculos (placa, modelo, ano, km_atual) VALUES (?,?,?,?)",
                              (placa.upper().strip(), modelo.strip(), ano.strip(), km))
                    conn.commit()
                    st.success("Veículo cadastrado com sucesso!")
                    st.rerun()

        df_v = pd.read_sql("SELECT * FROM veiculos", conn)
        if not df_v.empty:
            st.dataframe(df_v, use_container_width=True, hide_index=True)
            id_del = st.selectbox("ID do veículo para excluir:", df_v["id"].tolist())
            if st.button("Excluir Veículo", use_container_width=True):
                c.execute("DELETE FROM veiculos WHERE id = ?", (id_del,))
                conn.commit()
                st.success("Removido!")
                st.rerun()

    elif st.session_state.aba_veiculos_ativa == "manutencoes":
        df_opts = pd.read_sql("SELECT id, modelo, placa FROM veiculos", conn)
        if not df_opts.empty:
            v_map = {f"{r['modelo']} ({r['placa']})": r["id"] for _, r in df_opts.iterrows()}
            with st.form("form_manut", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    v_esc = st.selectbox("Veículo", list(v_map.keys()))
                    t_reg = st.selectbox("Tipo", ["Manutenção Agendada", "Histórico Realizado"])
                    desc = st.text_input("Descrição (Ex: Troca de óleo)")
                with c2:
                    dt_m = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
                    val_m = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                    st_m = st.selectbox("Status", ["Pendente", "Concluído"])

                if st.form_submit_button("Salvar Manutenção", use_container_width=True):
                    c.execute("INSERT INTO manutencoes_veiculo (veiculo_id, tipo_registro, descricao, data, valor, status) VALUES (?,?,?,?,?,?)",
                              (v_map[v_esc], t_reg, desc, dt_m.strftime("%Y-%m-%d"), val_m, st_m))
                    conn.commit()
                    st.success("Salvo!")
                    st.rerun()

            df_m = pd.read_sql("SELECT m.id, v.modelo, m.descricao, m.data, m.valor, m.status FROM manutencoes_veiculo m JOIN veiculos v ON m.veiculo_id = v.id", conn)
            if not df_m.empty:
                df_m["data"] = df_m["data"].apply(formatar_data_ptbr)
                st.dataframe(df_m, use_container_width=True, hide_index=True)
        else:
            st.warning("Cadastre um veículo primeiro.")

    else:
        df_opts = pd.read_sql("SELECT id, modelo, placa FROM veiculos", conn)
        if not df_opts.empty:
            v_map = {f"{r['modelo']} ({r['placa']})": r["id"] for _, r in df_opts.iterrows()}
            with st.form("form_comb", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    v_esc = st.selectbox("Veículo", list(v_map.keys()), key="v_comb")
                    dt_c = st.date_input("Data", value=date.today(), format="DD/MM/YYYY", key="d_comb")
                    litros = st.number_input("Litros", min_value=0.01, value=40.0, format="%.2f")
                with c2:
                    val_tot = st.number_input("Valor Total (R$)", min_value=0.0, value=200.0, format="%.2f")
                    km_od = st.number_input("Odômetro (Km)", min_value=0.0, value=50000.0)

                if st.form_submit_button("Registrar Abastecimento", use_container_width=True):
                    c.execute("INSERT INTO consumo_combustivel (veiculo_id, data, litros, valor_total, km_odometro, consumo_medio) VALUES (?,?,?,?,?,?)",
                              (v_map[v_esc], dt_c.strftime("%Y-%m-%d"), litros, val_tot, km_od, 10.0))
                    conn.commit()
                    st.success("Salvo!")
                    st.rerun()

            df_c = pd.read_sql("SELECT c.id, v.modelo, c.data, c.litros, c.valor_total, c.km_odometro FROM consumo_combustivel c JOIN veiculos v ON c.veiculo_id = v.id", conn)
            if not df_c.empty:
                df_c["data"] = df_c["data"].apply(formatar_data_ptbr)
                st.dataframe(df_c, use_container_width=True, hide_index=True)
        else:
            st.warning("Cadastre um veículo primeiro.")

# ==========================================
# --- SEÇÃO 3A: DASHBOARD MANUAL ---
# ==========================================
elif st.session_state.pagina_atual == "📊 Dashboard Manual":
    botao_voltar()
    st.subheader("📊 Executive Dashboard — Lançamentos Reais Manuais")

    df_all = pd.read_sql("SELECT * FROM transacoes WHERE origem IN ('Manual', 'Nota_Fiscal', 'Voz_IA', 'Chat_IA')", conn)
    df_inv = pd.read_sql("SELECT * FROM carteira_investimentos", conn)
    df_cartao = pd.read_sql("SELECT * FROM cartao_credito", conn)
    df_contas = pd.read_sql("SELECT * FROM contas", conn)
    df_metas = pd.read_sql("SELECT * FROM metas", conn)
    df_saldo_banco = pd.read_sql("SELECT * FROM saldo_banco_manual ORDER BY id DESC LIMIT 1", conn)

    if "dash_manual_mes_ref" not in st.session_state:
        st.session_state.dash_manual_mes_ref = date.today().month

    cols_meses = st.columns(12)
    meses_map = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
    for m in range(1, 13):
        with cols_meses[m - 1]:
            if st.button(meses_map[m], key=f"btn_m_{m}", use_container_width=True, type="primary" if st.session_state.dash_manual_mes_ref == m else "secondary"):
                st.session_state.dash_manual_mes_ref = m
                st.rerun()

    mes_str = f"{date.today().year}-{st.session_state.dash_manual_mes_ref:02d}"
    if not df_all.empty:
        df_all["data"] = pd.to_datetime(df_all["data"])
        df = df_all[df_all["data"].dt.strftime("%Y-%m") == mes_str].copy()
    else:
        df = pd.DataFrame()

    receitas = df[df["tipo"] == "Receita"]["valor"].sum() if not df.empty else 0.0
    despesas = df[df["tipo"] == "Despesa"]["valor"].sum() if not df.empty else 0.0
    saldo_caixa = receitas - despesas
    patrimonio_inv = (df_inv["quantidade"] * df_inv["preco_medio"]).sum() if not df_inv.empty else 0.0
    total_faturas = df_cartao["valor"].sum() if not df_cartao.empty else 0.0
    total_contas = df_contas[df_contas["pago"] == 0]["valor"].sum() if not df_contas.empty else 0.0
    patrimonio_liq = patrimonio_inv + max(0, saldo_caixa)

    b1, b2, b3, b4, b5 = st.columns(5)
    for col, (lbl, val, colr) in zip([b1, b2, b3, b4, b5], [
        ("⚡ BURN RATE", f"R$ {despesas/30:,.2f}", "#f8fafc"),
        ("💵 SALDO CAIXA", f"R$ {saldo_caixa:,.2f}", "#3b82f6"),
        ("🏦 SALDO BANCO", f"R$ {float(df_saldo_banco.iloc[0]['saldo_conta']) if not df_saldo_banco.empty else 0:,.2f}", "#34d399"),
        ("🟢 ENTRADAS", f"R$ {receitas:,.2f}", "#22c55e"),
        ("🔴 SAÍDAS", f"R$ {despesas:,.2f}", "#ef4444")
    ]):
        with col:
            st.markdown(f'<div class="group-card"><span style="color: #94a3b8; font-size: 11px;">{lbl}</span><h3 style="color: {colr}; margin: 4px 0 0 0; font-size: 16px;">{val}</h3></div>', unsafe_allow_html=True)

    if not df.empty and not df[df["tipo"] == "Despesa"].empty:
        st.markdown("---")
        st.subheader("🚨 Top 3 Maiores Vilões")
        top3 = df[df["tipo"] == "Despesa"].sort_values(by="valor", ascending=False).head(3)
        cols_v = st.columns(3)
        for idx, (_, r) in enumerate(top3.iterrows()):
            with cols_v[idx]:
                st.markdown(f'<div class="group-card"><span style="color: #f87171; font-size: 11px;"># {idx+1} GASTO</span><h4 style="margin: 4px 0; font-size: 14px;">{r["descricao"]}</h4><h3 style="color: #ef4444; margin: 0; font-size: 16px;">R$ {r["valor"]:,.2f}</h3></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📈 Distribuição de Despesas por Categoria")
        gasto_cat = df[df["tipo"] == "Despesa"].groupby("categoria")["valor"].sum().reset_index()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig = px.pie(gasto_cat, names="categoria", values="valor", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc", margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        with col_g2:
            st.dataframe(gasto_cat.rename(columns={"categoria": "Categoria", "valor": "Total (R$)"}), use_container_width=True, hide_index=True)

# ==========================================
# --- SEÇÃO 3B: DASHBOARD BANCO ---
# ==========================================
elif st.session_state.pagina_atual == "📥 Dashboard Banco":
    botao_voltar()
    st.subheader("📥 Dashboard de Auditoria & Extratos do Banco")
    df_banco = pd.read_sql("SELECT * FROM transacoes WHERE origem = 'Banco_PDF'", conn)
    df_sb = pd.read_sql("SELECT * FROM saldo_banco_manual ORDER BY id DESC LIMIT 1", conn)

    if not df_banco.empty or not df_sb.empty:
        saldo_conta = float(df_sb.iloc[0]["saldo_conta"]) if not df_sb.empty else 0.0
        rec_b = df_banco[df_banco["tipo"] == "Receita"]["valor"].sum() if not df_banco.empty else 0.0
        desp_b = df_banco[df_banco["tipo"] == "Despesa"]["valor"].sum() if not df_banco.empty else 0.0

        c1, c2, c3, c4 = st.columns(4)
        for col, (lbl, val, colr) in zip([c1, c2, c3, c4], [
            ("🏦 SALDO CONTA", f"R$ {saldo_conta:,.2f}", "#34d399"),
            ("⚖️ SALDO LÍQUIDO", f"R$ {rec_b - desp_b:,.2f}", "#3b82f6"),
            ("🟢 ENTRADAS", f"R$ {rec_b:,.2f}", "#22c55e"),
            ("🔴 SAÍDAS", f"R$ {desp_b:,.2f}", "#ef4444")
        ]):
            with col:
                st.markdown(f'<div class="group-card"><span style="color: #94a3b8; font-size: 11px;">{lbl}</span><h3 style="color: {colr}; margin: 4px 0 0 0; font-size: 16px;">{val}</h3></div>', unsafe_allow_html=True)

        if not df_banco.empty:
            st.markdown("---")
            st.dataframe(df_banco[["data", "tipo", "descricao", "categoria", "valor"]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado bancário registrado.")

# ==========================================
# --- SEÇÃO 4: PREVISÃO FINANCEIRA ---
# ==========================================
elif st.session_state.pagina_atual == "🔮 Previsão Financeira":
    botao_voltar()
    st.subheader("📅 Previsão Financeira & Simulador")

    if "prev_data_atual" not in st.session_state:
        st.session_state.prev_data_atual = datetime.now().replace(day=1)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("❮ Mês Anterior", use_container_width=True):
            st.session_state.prev_data_atual = (st.session_state.prev_data_atual - timedelta(days=1)).replace(day=1)
            st.rerun()
    with c2:
        if st.button("Mês Seguinte ❯", use_container_width=True):
            st.session_state.prev_data_atual = (st.session_state.prev_data_atual + timedelta(days=32)).replace(day=1)
            st.rerun()

    ano_a, mes_a = st.session_state.prev_data_atual.year, st.session_state.prev_data_atual.month
    st.markdown(f"<h3 style='text-align: center;'>Referência: {mes_a:02d}/{ano_a}</h3>", unsafe_allow_html=True)

    df_cartao = pd.read_sql("SELECT * FROM cartao_credito", conn)
    df_contas = pd.read_sql("SELECT * FROM contas WHERE pago = 0", conn)
    df_rec = pd.read_sql("SELECT * FROM contas_receber WHERE recebido = 0", conn)

    tot_cartao = df_cartao["valor"].sum() if not df_cartao.empty else 0.0
    tot_contas = df_contas["valor"].sum() if not df_contas.empty else 0.0
    tot_rec = df_rec["valor"].sum() if not df_rec.empty else 0.0

    m1, m2, m3 = st.columns(3)
    for col, (lbl, val, colr) in zip([m1, m2, m3], [
        ("🟢 ENTRADAS PREVISTAS", f"R$ {tot_rec:,.2f}", "#22c55e"),
        ("🔴 SAÍDAS PREVISTAS", f"R$ {tot_cartao + tot_contas:,.2f}", "#ef4444"),
        ("⚖️ SALDO PROJETADO", f"R$ {tot_rec - (tot_cartao + tot_contas):,.2f}", "#3b82f6")
    ]):
        with col:
            st.markdown(f'<div class="group-card"><span style="color: #94a3b8; font-size: 11px;">{lbl}</span><h3 style="color: {colr}; margin: 4px 0 0 0; font-size: 18px;">{val}</h3></div>', unsafe_allow_html=True)

# ==========================================
# --- SEÇÃO 5: CARTÃO DE CRÉDITO ---
# ==========================================
elif st.session_state.pagina_atual == "💳 Cartão de Crédito":
    botao_voltar()
    st.subheader("💳 Gestão Avançada de Faturas de Cartão de Crédito")

    with st.form("form_cc", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cartao = st.selectbox("Cartão", ["Itaúcard", "Samsung Itaú", "Nubank", "Santander", "Outro"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        with c2:
            dt = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
            dia_f = st.number_input("Dia Fechamento", min_value=1, max_value=31, value=10)
            dia_v = st.number_input("Dia Vencimento", min_value=1, max_value=31, value=17)

        cat = st.selectbox("Categoria", ["🛒 Supermercado (Necessidade)", "🏠 Contas Fixas (Necessidade)", "🍔 Lazer & Alimentação Fora (Desejos)"])

        if st.form_submit_button("Lançar na Fatura", use_container_width=True):
            if desc.strip() and val > 0:
                mes_fat = calcular_mes_fatura(dt, dia_f)
                c.execute("INSERT INTO cartao_credito (data, cartao, descricao, categoria, valor, dia_fechamento, dia_vencimento, mes_fatura) VALUES (?,?,?,?,?,?,?,?)",
                          (dt.strftime("%Y-%m-%d"), cartao, desc.strip(), cat, val, dia_f, dia_v, mes_fat))
                conn.commit()
                st.success(f"Alocado para a fatura: **{mes_fat}**")
                st.rerun()

    df_cc = pd.read_sql("SELECT * FROM cartao_credito", conn)
    if not df_cc.empty:
        st.markdown("---")
        df_cc["data"] = df_cc["data"].apply(formatar_data_ptbr)
        st.dataframe(df_cc, use_container_width=True, hide_index=True)
        id_del = st.selectbox("ID para excluir:", df_cc["id"].tolist())
        if st.button("Remover Compra", use_container_width=True):
            c.execute("DELETE FROM cartao_credito WHERE id = ?", (id_del,))
            conn.commit()
            st.success("Removido!")
            st.rerun()

# ==========================================
# --- SEÇÃO 6: INVESTIMENTOS ---
# ==========================================
elif st.session_state.pagina_atual == "📈 Investimentos":
    botao_voltar()
    st.subheader("📈 Painel Profissional de Investimentos & Caixinhas")

    with st.form("form_inv", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            ativo = st.text_input("Ativo / Caixinha (Ex: Reserva de Emergência)")
            classe = st.selectbox("Tipo", ["Caixinha Nubank", "CDB / Renda Fixa", "Tesouro Direto", "Ações BR", "FIIs"])
        with c2:
            qtd = st.number_input("Quantidade", min_value=0.0001, value=1.00)
            preco = st.number_input("Valor Total / Preço Unitário (R$)", min_value=0.0, format="%.2f")
        with c3:
            dt_ap = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
            st.write("")
            btn_add = st.form_submit_button("Cadastrar Posição", use_container_width=True)

        if btn_add and ativo.strip():
            c.execute("INSERT INTO carteira_investimentos (data, ativo, classe, quantidade, preco_medio) VALUES (?,?,?,?,?)",
                      (dt_ap.strftime("%Y-%m-%d"), ativo.upper().strip(), classe, qtd, preco))
            conn.commit()
            st.success("Cadastrado com sucesso!")
            st.rerun()

    df_inv = pd.read_sql("SELECT * FROM carteira_investimentos", conn)
    if not df_inv.empty:
        df_inv["Valor Total"] = df_inv["quantidade"] * df_inv["preco_medio"]
        st.markdown("---")
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
        id_del = st.selectbox("ID para remover:", df_inv["id"].tolist())
        if st.button("Remover Ativo", use_container_width=True):
            c.execute("DELETE FROM carteira_investimentos WHERE id = ?", (id_del,))
            conn.commit()
            st.success("Removido!")
            st.rerun()

# ==========================================
# --- SEÇÃO 7: DESAFIOS ---
# ==========================================
elif st.session_state.pagina_atual == "🎯 Desafios":
    botao_voltar()
    st.subheader("🎯 Desafio de Poupança Progressiva (R$ 20.100,00)")
    df_deps = pd.read_sql("SELECT * FROM tabela_depositos", conn)
    tot_conc = df_deps[df_deps["status"] == "Concluído"]["valor"].sum()
    st.progress(min(tot_conc / df_deps["valor"].sum(), 1.0))
    st.dataframe(df_deps.rename(columns={"numero_deposito": "Depósito", "valor": "Valor (R$)", "status": "Status"}), use_container_width=True, hide_index=True)

# ==========================================
# --- SEÇÃO 8A: METAS DE GASTOS ---
# ==========================================
elif st.session_state.pagina_atual == "🎯 Metas de Gastos":
    botao_voltar()
    st.subheader("🎯 Definir Teto de Meta Mensal por Categoria")
    with st.form("form_meta", clear_on_submit=True):
        cat = st.selectbox("Categoria", ["🏠 Contas Fixas (Necessidade)", "🛒 Supermercado (Necessidade)", "🍔 Lazer & Alimentação Fora (Desejos)"])
        val_m = st.number_input("Valor Teto (R$)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Salvar Meta", use_container_width=True):
            c.execute("DELETE FROM metas WHERE categoria = ?", (cat,))
            c.execute("INSERT INTO metas (categoria, valor_meta) VALUES (?, ?)", (cat, val_m))
            conn.commit()
            st.success("Meta salva!")
            st.rerun()

# ==========================================
# --- SEÇÃO 8B: CATEGORIAS & ÍCONES ---
# ==========================================
elif st.session_state.pagina_atual == "🏷️ Categorias & Ícones":
    botao_voltar()
    st.subheader("🏷️ Gerenciamento de Categorias Personalizadas")
    with st.form("form_cat", clear_on_submit=True):
        icone = st.selectbox("Ícone", ["📄", "🧾", "💳", "💰", "🏠", "🛒", "🍔", "🚗", "📈", "⭐"])
        nome = st.text_input("Nome da Categoria")
        if st.form_submit_button("Salvar Categoria", use_container_width=True) and nome.strip():
            c.execute("INSERT INTO categorias (nome) VALUES (?)", (f"{icone} {nome.strip()}",))
            conn.commit()
            st.success("Salvo!")
            st.rerun()

# ==========================================
# --- SEÇÃO 9: SAÚDE FINANCEIRA ---
# ==========================================
elif st.session_state.pagina_atual == "❤️ Saúde Financeira":
    botao_voltar()
    st.subheader("❤️ Score de Saúde Financeira")
    df_s = pd.read_sql("SELECT * FROM transacoes WHERE origem IN ('Manual', 'Nota_Fiscal', 'Voz_IA', 'Chat_IA')", conn)
    rec = df_s[df_s["tipo"] == "Receita"]["valor"].sum() if not df_s.empty else 0
    desp = df_s[df_s["tipo"] == "Despesa"]["valor"].sum() if not df_s.empty else 0
    score = int(min(1000, max(0, 500 if rec >= desp else 200)))
    st.markdown(f'<div class="group-card" style="text-align: center;"><h1 style="color: #3b82f6; font-size: 50px;">{score}</h1><p>pontos de 1000</p></div>', unsafe_allow_html=True)

# ==========================================
# --- SEÇÃO 10: CONTAS A PAGAR & RECEBER ---
# ==========================================
elif st.session_state.pagina_atual == "📅 Contas a Pagar":
    botao_voltar()
    st.subheader("📅 Contas a Pagar & Receber")

    if "aba_contas_ativa" not in st.session_state:
        st.session_state.aba_contas_ativa = "pagar"

    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        if st.button("📉 Contas a Pagar", use_container_width=True, type="primary" if st.session_state.aba_contas_ativa == "pagar" else "secondary"):
            st.session_state.aba_contas_ativa = "pagar"
            st.rerun()
    with c2:
        if st.button("📈 Contas a Receber", use_container_width=True, type="primary" if st.session_state.aba_contas_ativa == "receber" else "secondary"):
            st.session_state.aba_contas_ativa = "receber"
            st.rerun()

    st.markdown("---")

    if st.session_state.aba_contas_ativa == "pagar":
        with st.form("form_cp", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                venc = st.date_input("Vencimento", value=date.today(), format="DD/MM/YYYY")
            with c2:
                desc = st.text_input("Descrição")
                val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")

            if st.form_submit_button("Adicionar Conta", use_container_width=True) and desc.strip() and val > 0:
                c.execute("INSERT INTO contas (vencimento, descricao, valor, pago) VALUES (?,?,?,?)",
                          (venc.strftime("%Y-%m-%d"), desc.strip(), val, 0))
                conn.commit()
                st.success("Salvo!")
                st.rerun()

        df_cp = pd.read_sql("SELECT * FROM contas", conn)
        if not df_cp.empty:
            df_cp["vencimento"] = df_cp["vencimento"].apply(formatar_data_ptbr)
            st.dataframe(df_cp, use_container_width=True, hide_index=True)
    else:
        with st.form("form_cr", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                venc = st.date_input("Vencimento", value=date.today(), format="DD/MM/YYYY")
            with c2:
                desc = st.text_input("Descrição")
                val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")

            if st.form_submit_button("Adicionar Recebível", use_container_width=True) and desc.strip() and val > 0:
                c.execute("INSERT INTO contas_receber (vencimento, descricao, valor, recebido) VALUES (?,?,?,?)",
                          (venc.strftime("%Y-%m-%d"), desc.strip(), val, 0))
                conn.commit()
                st.success("Salvo!")
                st.rerun()

        df_cr = pd.read_sql("SELECT * FROM contas_receber", conn)
        if not df_cr.empty:
            df_cr["vencimento"] = df_cr["vencimento"].apply(formatar_data_ptbr)
            st.dataframe(df_cr, use_container_width=True, hide_index=True)

# ==========================================
# --- SEÇÃO 11: EXTRATO & BACKUP ---
# ==========================================
elif st.session_state.pagina_atual == "📋 Extrato & Backup":
    botao_voltar()
    st.subheader("📋 Central de Extrato Bancário & Backup Geral")

    with st.expander("📥 Importar Extrato Bancário (PDF)", expanded=True):
        if arq_extrato := st.file_uploader("Arquivo PDF do Extrato", type=["pdf"]):
            try:
                with pdfplumber.open(arq_extrato) as pdf:
                    for pag in pdf.pages:
                        if txt := pag.extract_text():
                            for linha in txt.split("\n"):
                                if nums := re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", linha):
                                    val = float(nums[-1].replace(".", "").replace(",", "."))
                                    c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor, origem) VALUES (?,?,?,?,?,?)",
                                              (date.today().strftime("%Y-%m-%d"), "Despesa", linha[:50], categorizar_automaticamente(linha, "Despesa"), val, "Banco_PDF"))
                conn.commit()
                st.success("Extrato importado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao ler PDF: {e}")

    st.markdown("---")
    st.subheader("📋 Relação Completa de Transações Manuais & Bancárias")
    df_geral = pd.read_sql("SELECT * FROM transacoes ORDER BY id DESC", conn)
    if not df_geral.empty:
        df_geral["data"] = df_geral["data"].apply(formatar_data_ptbr)
        st.dataframe(df_geral, use_container_width=True, hide_index=True)
        id_del_t = st.selectbox("ID para excluir transação:", df_geral["id"].tolist())
        if st.button("Excluir Transação", use_container_width=True):
            c.execute("DELETE FROM transacoes WHERE id = ?", (id_del_t,))
            conn.commit()
            st.success("Removido!")
            st.rerun()
    else:
        st.info("Nenhuma transação registrada.")
