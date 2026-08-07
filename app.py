import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Gestor Financeiro Profissional", page_icon="💸", layout="wide"
)

# Estilo visual moderno injetado via CSS
st.markdown(
    """
    <style>
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
            background: rgba(18, 21, 28, 0.5);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }

        .group-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cabeçalho Principal
st.markdown(
    """
    <div class="header-title"><span>💸</span> Gestor Financeiro Profissional</div>
    <div class="header-subtitle">Sistema avançado de controle orçamentário, investimentos, projeções e auditoria de holerites.</div>
    
    <div class="section-indicator">
        <h2><span>🎛️</span> Painel de Indicadores & Acesso Rápido</h2>
        <p>Clique em um dos botões abaixo para acessar a respectiva seção do sistema:</p>
    </div>
""",
    unsafe_allow_html=True,
)

# Inicializa o controle de navegação se não existir
if "pagina_atual" not in st.session_state:
  st.session_state.pagina_atual = "Home"

# ---------------------------------------------------------
# GRUPO 1: Painel de Gestão Diária
# ---------------------------------------------------------
st.markdown(
    '<div class="group-card"><div class="group-title">Painel de Gestão'
    " Diária</div>",
    unsafe_allow_html=True,
)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
  if st.button("🔴 Lançar Despesa", use_container_width=True):
    st.session_state.pagina_atual = "Lançar Despesa"
with col2:
  if st.button("🟢 Entradas & Salários", use_container_width=True):
    st.session_state.pagina_atual = "Entradas & Salários"
with col3:
  if st.button("📅 Contas a Pagar", use_container_width=True):
    st.session_state.pagina_atual = "Contas a Pagar"
with col4:
  if st.button("💳 Cartão de Crédito", use_container_width=True):
    st.session_state.pagina_atual = "Cartão de Crédito"
with col5:
  if st.button("📊 Fluxo de Caixa", use_container_width=True):
    st.session_state.pagina_atual = "Fluxo de Caixa"
st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# GRUPO 2: Análise & Planejamento
# ---------------------------------------------------------
st.markdown(
    '<div class="group-card"><div class="group-title">Análise &'
    " Planejamento</div>",
    unsafe_allow_html=True,
)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
  if st.button("📈 Investimentos", use_container_width=True):
    st.session_state.pagina_atual = "Investimentos"
with col2:
  if st.button("🔮 Projeções Futuras", use_container_width=True):
    st.session_state.pagina_atual = "Projeções Futuras"
with col3:
  if st.button("📊 Dashboard Geral", use_container_width=True):
    st.session_state.pagina_atual = "Dashboard Geral"
with col4:
  if st.button("🎯 Desafios", use_container_width=True):
    st.session_state.pagina_atual = "Desafios"
with col5:
  if st.button("🎯 Metas de Gastos", use_container_width=True):
    st.session_state.pagina_atual = "Metas de Gastos"
st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# GRUPO 3 & 4: Configuração, Suporte, Relatórios & Backup
# ---------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
  st.markdown(
      '<div class="group-card"><div class="group-title">Configuração &'
      " Suporte</div>",
      unsafe_allow_html=True,
  )
  sub1, sub2 = st.columns(2)
  with sub1:
    if st.button("🏷️ Categorias & Ícones", use_container_width=True):
      st.session_state.pagina_atual = "Categorias & Ícones"
  with sub2:
    if st.button("❤️ Saúde Financeira", use_container_width=True):
      st.session_state.pagina_atual = "Saúde Financeira"
  st.markdown("</div>", unsafe_allow_html=True)

with col_b:
  st.markdown(
      '<div class="group-card"><div class="group-title">Relatórios &'
      " Backup</div>",
      unsafe_allow_html=True,
  )
  sub1, sub2 = st.columns(2)
  with sub1:
    if st.button("📄 Holerites & PDF", use_container_width=True):
      st.session_state.pagina_atual = "Holerites & PDF"
  with sub2:
    if st.button("📋 Extrato & Backup", use_container_width=True):
      st.session_state.pagina_atual = "Extrato & Backup"
  st.markdown("</div>", unsafe_allow_html=True)

# Exemplo de roteamento baseado na escolha do usuário
st.write("---")
st.info(f"Seção ativa no momento: **{st.session_state.pagina_atual}**")
