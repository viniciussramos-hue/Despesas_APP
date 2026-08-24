from datetime import datetime, date
import os
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA (ESTILO 100% GESTORMONEY)
# ==========================================
st.set_page_config(
    page_title="GestorMoney - Seu Aliado Financeiro",
    page_icon="💰",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Fundo geral e paleta de cores inspirada no GestorMoney */
    .main { background-color: #0c101d; color: #e5e7eb; }
    .stSidebar { background-color: #121826; border-right: 1px solid #1f2937; }
    
    /* Estilização dos Cards idênticos à referência */
    .gm-card {
        background-color: #161e2e;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #1f2937;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .gm-card-title {
        color: #9ca3af;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .gm-card-value {
        font-size: 24px;
        font-weight: 700;
        margin: 8px 0;
    }
    .gm-card-footer {
        color: #6b7280;
        font-size: 11px;
    }
    h1, h2, h3 { color: #f9fafb !important; }
    
    /* Botão verde de destaque */
    .btn-verde button {
        background-color: #a3e635 !important;
        color: #000 !important;
        font-weight: bold !important;
        border: none !important;
    }
    .btn-verde button:hover {
        background-color: #bef264 !important;
        color: #000 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# BANCO DE DADOS E MIGRATIONS (SQLite)
# ==========================================
DB_NAME = "gestormoney_original.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            valor REAL,
            data TEXT,
            categoria TEXT,
            observacoes TEXT,
            recorrente INTEGER DEFAULT 0
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            valor REAL,
            data TEXT,
            categoria TEXT,
            observacoes TEXT,
            recorrente INTEGER DEFAULT 0
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            tipo TEXT,
            icone TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT,
            total_investido REAL,
            valor_mercado REAL
        )
    """)

  # Insere categorias padrão se a tabela estiver vazia
  cursor.execute("SELECT COUNT(*) FROM categorias")
  if cursor.fetchone()[0] == 0:
    padroes = [
        ("Alimentação", "Despesa", "🍔"),
        ("Aluguel", "Despesa", "🏠"),
        ("Salário", "Receita", "💵"),
        ("Freelance", "Receita", "💻"),
        ("Combustível", "Despesa", "⛽"),
        ("Lazer", "Despesa", "🎮"),
        ("Investimentos", "Receita", "📈"),
        ("Saúde", "Despesa", "💊"),
    ]
    cursor.executemany(
        "INSERT INTO categorias (nome, tipo, icone) VALUES (?, ?, ?)", padroes
    )

  conn.commit()
  conn.close()


init_db()

# Listas auxiliares
CATEGORIAS_DESPESAS = [
    "Alimentação",
    "Aluguel",
    "Combustível",
    "Lazer",
    "Saúde",
    "Outros",
]
CATEGORIAS_RECEITAS = ["Salário", "Freelance", "Investimentos", "Outros"]


# ==========================================
# MENU LATERAL COM BOTÕES PERSONALIZADOS
# ==========================================
st.sidebar.markdown(
    """
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
        <div style='background: #f59e0b; padding: 8px; border-radius: 8px; font-weight: bold; color: #000;'>🤖</div>
        <div>
            <span style='font-size: 16px; font-weight: bold; color: #fff;'>GestorMoney</span><br>
            <span style='font-size: 11px; color: #9ca3af;'>SEU ALIADO FINANCEIRO</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<p style='color: #9ca3af; font-size: 12px; margin-bottom: 10px;'>"
    "Navegação Principal</p>",
    unsafe_allow_html=True,
)

if "menu_ativo" not in st.session_state:
  st.session_state["menu_ativo"] = "Dashboard"

if st.sidebar.button(
    "📊 Dashboard",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Dashboard"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Dashboard"
  st.rerun()

if st.sidebar.button(
    "📈 Receitas",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Receitas"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Receitas"
  st.rerun()

if st.sidebar.button(
    "📉 Despesas",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Despesas"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Despesas"
  st.rerun()

if st.sidebar.button(
    "📁 Categorias",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Categorias"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Categorias"
  st.rerun()

menu = st.session_state["menu_ativo"]
conn = sqlite3.connect(DB_NAME)

# ==========================================
# MÓDULO: DASHBOARD
# ==========================================
if menu == "Dashboard":
  col_head1, col_head2 = st.columns([3, 1])
  with col_head1:
    st.markdown(
        "<h1 style='margin-bottom: 0;'>Dashboard</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color: #9ca3af; margin-top: 0;'>Bem-vindo de volta,"
        " Vinicius Ramos</p>",
        unsafe_allow_html=True,
    )
  with col_head2:
    st.markdown(
        """
        <div style='background-color: #161e2e; border: 1px solid #1f2937; padding: 8px 15px; border-radius: 20px; text-align: right; display: flex; align-items: center; justify-content: flex-end; gap: 10px;'>
            <span style='color: #f59e0b; font-weight: bold;'>❤️ 375</span>
            <span style='background: #10b981; color: #000; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;'>Atenção</span>
            <span style='background: #374151; color: #fff; padding: 4px 8px; border-radius: 50%; font-size: 11px; font-weight: bold;'>VR</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown(
      """
      <div style='background-color: #161e2e; border: 1px solid #1f2937; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; font-size: 14px;'>
          <span style='color: #f59e0b; font-weight: bold;'>🏆 0/9</span>
          <span style='color: #6b7280;'>|</span>
          <span>🎯 🪙 🛡️ 📊 💡 🚀 👑 ⚡</span>
      </div>
  """,
      unsafe_allow_html=True,
  )

  df_desp = pd.read_sql("SELECT * FROM despesas", conn)
  df_rec = pd.read_sql("SELECT * FROM receitas", conn)
  df_inv = pd.read_sql("SELECT * FROM investimentos", conn)

  total_despesas = df_desp["valor"].sum() if not df_desp.empty else 0.0
  total_receitas = df_rec["valor"].sum() if not df_rec.empty else 0.0
  saldo_caixa = total_receitas - total_despesas

  total_investido = (
      df_inv["total_investido"].sum() if not df_inv.empty else 0.0
  )
  valor_mercado = df_inv["valor_mercado"].sum() if not df_inv.empty else 0.0
  lucro_inv = valor_mercado - total_investido
  patrimonio_total = total_investido + saldo_caixa

  col_c1, col_c2 = st.columns(2)
  with col_c1:
    st.markdown(
        f"""
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="gm-card-title">💰 Disponível em Caixa</span>
                <span style="color: #10b981; font-size: 16px;">👁️</span>
            </div>
            <div class="gm-card-value" style="color: #10b981;">R$ {saldo_caixa:,.2f}</div>
            <div class="gm-card-footer">Receitas: R$ {total_receitas:,.2f} | Despesas: R$ {total_despesas:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with col_c2:
    st.markdown(
        f"""
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="gm-card-title">📈 Investimentos</span>
                <span style="color: #10b981; font-size: 16px;">📈</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                <div>
                    <span style="color: #6b7280; font-size: 11px;">Total Investido</span><br>
                    <b style="font-size: 15px;">R$ {total_investido:,.2f}</b>
                </div>
                <div>
                    <span style="color: #6b7280; font-size: 11px;">Valor de Mercado</span><br>
                    <b style="font-size: 15px;">R$ {valor_mercado:,.2f}</b>
                </div>
                <div>
                    <span style="color: #6b7280; font-size: 11px;">Lucro</span><br>
                    <b style="font-size: 15px; color: #10b981;">+R$ {lucro_inv:,.2f}</b>
                </div>
            </div>
            <div style="margin-top: 15px; font-size: 13px; color: #e5e7eb; display: flex; justify-content: space-between; border-top: 1px solid #1f2937; padding-top: 10px;">
                <span>Patrimônio Total</span>
                <b style="font-size: 18px; color: #10b981;">R$ {patrimonio_total:,.2f}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# MÓDULO: CATEGORIAS (NOVO MÓDULO IDÊNTICO À REFERÊNCIA)
# ==========================================
elif menu == "Categorias":
  c_t1, c_t2 = st.columns([3, 1])
  with c_t1:
    st.markdown(
        "<h1 style='margin-bottom: 0;'>Categorias</h1>", unsafe_allow_html=True
    )
  with c_t2:
    st.markdown('<div class="btn-verde">', unsafe_allow_html=True)
    nova_cat_btn = st.button("＋ Nova Categoria", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

  # Barra de busca rápida
  busca_cat = st.text_input(
      "Busca",
      placeholder="🔍 Buscar categoria...",
      label_visibility="collapsed",
  )

  # Abas de Filtro superiores (Todas, Receitas, Despesas, Cartão)
  aba_cat = st.radio(
      "Filtro Categorias",
      ["Todas", "Receitas", "Despesas", "Cartão"],
      horizontal=True,
      label_visibility="collapsed",
  )

  st.markdown("<br>", unsafe_allow_html=True)

  # Modal / Painel de Cadastro de Nova Categoria
  if nova_cat_btn or st.session_state.get("abrir_modal_categoria", False):
    st.session_state["abrir_modal_categoria"] = True

    with st.container():
      st.markdown(
          """
            <div style='background-color: #161e2e; border: 1px solid #374151; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);'>
                <h3 style='margin-top: 0; color: #fff;'>Nova Categoria</h3>
            """,
          unsafe_allow_html=True,
      )

      with st.form("form_nova_categoria", clear_on_submit=True):
        nome_cat = st.text_input("Nome da Categoria", placeholder="Ex: Educação")
        tipo_cat = st.selectbox("Tipo", ["Despesa", "Receita"])
        icone_cat = st.text_input(
            "Ícone (Emoji)", placeholder="Ex: 📚", value="📁"
        )

        col_b1, col_b2 = st.columns(2)
        with col_b1:
          salvar_cat = st.form_submit_button(
              "Salvar Categoria", use_container_width=True, type="primary"
          )
        with col_b2:
          fechar_cat = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar_cat:
          if nome_cat:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categorias (nome, tipo, icone) VALUES (?, ?, ?)",
                (nome_cat, tipo_cat, icone_cat),
            )
            conn.commit()
            st.session_state["abrir_modal_categoria"] = False
            st.success("Categoria cadastrada com sucesso!")
            st.rerun()
          else:
            st.warning("Informe o nome da categoria.")

        if fechar_cat:
          st.session_state["abrir_modal_categoria"] = False
          st.rerun()

      st.markdown("</div>", unsafe_allow_html=True)

  # Leitura do Banco de Dados
  df_categorias = pd.read_sql("SELECT * FROM categorias", conn)

  # Aplicação dos filtros
  if not df_categorias.empty:
    if aba_cat == "Receitas":
      df_categorias = df_categorias[df_categorias["tipo"] == "Receita"]
    elif aba_cat == "Despesas":
      df_categorias = df_categorias[df_categorias["tipo"] == "Despesa"]

    if busca_cat:
      df_categorias = df_categorias[
          df_categorias["nome"].str.contains(busca_cat, case=False, na=False)
      ]

  # Exibição em Grade Estilizada de Cards
  if df_categorias.empty:
    st.markdown(
        """
        <div style='text-align: center; padding: 40px; background-color: #161e2e; border: 1px solid #1f2937; border-radius: 12px;'>
            <p style='color: #9ca3af;'>Nenhuma categoria encontrada.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
  else:
    cols_por_linha = 4
    linhas = [
        df_categorias.irow(i : i + cols_por_linha)
        for i in range(0, len(df_categorias), cols_por_linha)
    ]
    # Iteração segura em grid utilizando pandas
    for i in range(0, len(df_categorias), cols_por_linha):
      subset = df_categorias.iloc[i : i + cols_por_linha]
      cols = st.columns(cols_por_linha)
      for idx, (_, row) in enumerate(subset.iterrows()):
        with cols[idx]:
          cor_tipo = (
              "#10b981" if row["tipo"] == "Receita" else "#ef4444"
          )  # Verde ou Vermelho
          st.markdown(
              f"""
                <div class="gm-card" style="padding: 15px; text-align: left;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 20px;">{row['icone']}</span>
                        <span style="background-color: {cor_tipo}22; color: {cor_tipo}; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;">{row['tipo']}</span>
                    </div>
                    <div style="font-weight: bold; margin-top: 10px; font-size: 14px; color: #fff;">{row['nome']}</div>
                </div>
                """,
              unsafe_allow_html=True,
          )


# ==========================================
# MÓDULOS DE RECEITAS E DESPESAS (JÁ EXISTENTES)
# ==========================================
elif menu in ["Receitas", "Despesas"]:
  tabela = menu.lower()
  titulo = menu
  categorias = (
      CATEGORIAS_RECEITAS if menu == "Receitas" else CATEGORIAS_DESPESAS
  )
  cor_botao = "btn-verde" if menu == "Receitas" else "primary"

  c_t1, c_t2, c_t3 = st.columns([2, 2, 1])
  with c_t1:
    st.markdown(
        f"<h1 style='margin-bottom: 0;'>{titulo}</h1>", unsafe_allow_html=True
    )

  df_dados = pd.read_sql(f"SELECT * FROM {tabela}", conn)
  total_geral = df_dados["valor"].sum() if not df_dados.empty else 0.0

  with c_t2:
    st.markdown(
        f"<p style='color: #9ca3af; margin-top: 10px;'>Total: <b style='color:"
        f" #f9fafb;'>R$ {total_geral:,.2f}</b></p>",
        unsafe_allow_html=True,
    )

  with c_t3:
    if cor_botao == "btn-verde":
      st.markdown('<div class="btn-verde">', unsafe_allow_html=True)
      nova_btn = st.button("＋ Nova", use_container_width=True)
      st.markdown("</div>", unsafe_allow_html=True)
    else:
      nova_btn = st.button("＋ Nova", use_container_width=True, type="primary")

  aba = st.radio(
      "Abas",
      ["📋 Simples", "🔄 Recorrentes", "📊 Avançada"],
      horizontal=True,
      label_visibility="collapsed",
  )
  st.markdown("<br>", unsafe_allow_html=True)

  if nova_btn or st.session_state.get(f"abrir_modal_{tabela}", False):
    st.session_state[f"abrir_modal_{tabela}"] = True
    with st.container():
      st.markdown(
          f"""
            <div style='background-color: #161e2e; border: 1px solid #374151; padding: 25px; border-radius: 12px; margin-bottom: 25px;'>
                <h3 style='margin-top: 0; color: #fff;'>Nova {titulo[:-1]}</h3>
            """,
          unsafe_allow_html=True,
      )
      with st.form(f"form_novo_{tabela}", clear_on_submit=True):
        desc = st.text_input("Descrição", placeholder="Ex: Descrição...")
        v1, v2 = st.columns(2)
        with v1:
          val = st.number_input(
              "Valor (R$)", min_value=0.00, format="%.2f", value=0.00
          )
        with v2:
          dt = st.date_input("Data", datetime.today())
        cat = st.selectbox("Categoria", categorias)
        obs = st.text_area("Observações")
        rec = st.toggle("Recorrente")

        b1, b2 = st.columns(2)
        with b1:
          salvar = st.form_submit_button(
              "Salvar", use_container_width=True, type="primary"
          )
        with b2:
          fechar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar and desc and val > 0:
          cursor = conn.cursor()
          cursor.execute(
              f"INSERT INTO {tabela} (descricao, valor, data, categoria,"
              " observacoes, recorrente) VALUES (?, ?, ?, ?, ?, ?)",
              (desc, val, str(dt), cat, obs, 1 if rec else 0),
          )
          conn.commit()
          st.session_state[f"abrir_modal_{tabela}"] = False
          st.rerun()
        if fechar:
          st.session_state[f"abrir_modal_{tabela}"] = False
          st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

  if not df_dados.empty:
    df_dados["Ícone"] = "📁"
    st.dataframe(
        df_dados[["data", "Ícone", "descricao", "categoria", "valor"]],
        use_container_width=True,
    )
  else:
    st.info(f"Nenhuma {titulo.lower()} cadastrada.")

conn.close()
