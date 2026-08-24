from datetime import datetime
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
        CREATE TABLE IF NOT EXISTS contas_futuras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vencimento TEXT,
            descricao TEXT,
            valor REAL,
            tipo TEXT,
            categoria TEXT,
            status TEXT DEFAULT 'Pendente'
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

  conn.commit()
  conn.close()


init_db()

# ==========================================
# LISTAS DE CATEGORIAS
# ==========================================
CATEGORIAS_DESPESAS = [
    "Alimentação",
    "Supermercado",
    "Moradia",
    "Transporte",
    "Combustível",
    "Saúde",
    "Lazer",
    "Serviços",
    "Outros",
]

CATEGORIAS_RECEITAS = [
    "Salário",
    "Freelance",
    "Investimentos",
    "Vendas",
    "Reembolso",
    "Outros",
]


def obter_icone_despesa(categoria):
  icones = {
      "Alimentação": "🍔",
      "Supermercado": "🛒",
      "Moradia": "🏠",
      "Transporte": "🚗",
      "Combustível": "⛽",
      "Saúde": "💊",
      "Lazer": "🎮",
      "Serviços": "💡",
      "Outros": "📦",
  }
  return icones.get(categoria, "📁")


def obter_icone_receita(categoria):
  icones = {
      "Salário": "💵",
      "Freelance": "💻",
      "Investimentos": "📈",
      "Vendas": "🏷️",
      "Reembolso": "🔄",
      "Outros": "💰",
  }
  return icones.get(categoria, "📁")


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
            <div style="margin-top: 15px; font-size: 13px; color: #e5e7eb; display: flex; justify-content: space-between; border-top: 1px solid #1f2937; padding-top: 10px;">
                <span>✨ Previsão fim do mês</span>
                <b style="color: #3b82f6;">R$ {saldo_caixa:,.2f} ▾</b>
            </div>
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
                <span>Patrimônio Total<br><span style="color: #6b7280; font-size: 11px;">Caixa + investimentos</span></span>
                <b style="font-size: 18px; color: #10b981;">R$ {patrimonio_total:,.2f}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  dc1, dc2, dc3, dc4 = st.columns(4)

  with dc1:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">📉 Dívida Total</div>
            <div class="gm-card-value" style="color: #ef4444;">R$ 0,00</div>
            <div class="gm-card-footer">Cartões + contas + financiamentos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc2:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">↗️ Contas a Receber Este Mês</div>
            <div class="gm-card-value" style="color: #10b981;">R$ {total_receitas:,.2f}</div>
            <div class="gm-card-footer">Total de receitas cadastradas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc3:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">📅 Contas a Pagar Este Mês</div>
            <div class="gm-card-value" style="color: #f59e0b;">R$ {total_despesas:,.2f}</div>
            <div class="gm-card-footer">Total de despesas cadastradas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc4:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">💳 Limite Disponível Cartões</div>
            <div class="gm-card-value" style="color: #3b82f6;">R$ 0,00</div>
            <div class="gm-card-footer">Limite total: R$ 0,00</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.divider()

  gc1, gc2 = st.columns(2)
  with gc1:
    st.subheader("Fluxo de Caixa Pessoal")
    st.markdown(
        "<p style='color: #6b7280; font-size: 12px;'>Movimentação financeira"
        " geral</p>",
        unsafe_allow_html=True,
    )
    if not df_desp.empty or not df_rec.empty:
      chart_data = pd.DataFrame(
          {
              "Receitas": df_rec["valor"].tolist()
              if not df_rec.empty
              else [0],
              "Despesas": df_desp["valor"].tolist()
              if not df_desp.empty
              else [0],
          }
      )
      st.bar_chart(chart_data)
    else:
      st.info("Sem dados de movimentação para o gráfico.")

  with gc2:
    st.subheader("Comparativo Semanal")
    st.markdown(
        "<p style='color: #6b7280; font-size: 12px;'>Receitas vs Despesas</p>",
        unsafe_allow_html=True,
    )
    if not df_desp.empty or not df_rec.empty:
      st.line_chart(chart_data)
    else:
      st.info("Sem dados suficientes para o comparativo.")

# ==========================================
# MÓDULO: RECEITAS
# ==========================================
elif menu == "Receitas":
  c_t1, c_t2, c_t3 = st.columns([2, 2, 1])
  with c_t1:
    st.markdown(
        "<h1 style='margin-bottom: 0;'>Receitas</h1>", unsafe_allow_html=True
    )

  df_receitas = pd.read_sql("SELECT * FROM receitas", conn)
  total_geral_receitas = (
      df_receitas["valor"].sum() if not df_receitas.empty else 0.0
  )
  qtd_receitas = len(df_receitas)

  with c_t2:
    st.markdown(
        f"<p style='color: #9ca3af; margin-top: 10px;'>Total: <b style='color:"
        f" #f9fafb;'>R$ {total_geral_receitas:,.2f}</b></p>",
        unsafe_allow_html=True,
    )

  with c_t3:
    nova_rec_btn = st.button(
        "➕ Nova", use_container_width=True, type="primary"
    )

  # Barra de Filtros
  st.markdown('<div class="gm-card" style="padding: 15px;">', unsafe_allow_html=True)
  f1, f2 = st.columns(2)
  with f1:
    busca_termo = st.text_input(
        "Busca", placeholder="🔍 Buscar receita...", label_visibility="collapsed"
    )
  with f2:
    filtro_cat = st.selectbox(
        "Categoria",
        ["Todas as categorias"] + CATEGORIAS_RECEITAS,
        label_visibility="collapsed",
    )
  st.markdown("</div>", unsafe_allow_html=True)

  # Painel de Cadastro de Nova Receita
  if nova_rec_btn or st.session_state.get("abrir_modal_receita", False):
    st.session_state["abrir_modal_receita"] = True

    with st.container():
      st.markdown(
          """
            <div style='background-color: #161e2e; border: 1px solid #374151; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);'>
                <h3 style='margin-top: 0; color: #fff;'>Nova Receita</h3>
            """,
          unsafe_allow_html=True,
      )

      with st.form("form_nova_receita", clear_on_submit=True):
        desc = st.text_input("Descrição", placeholder="Ex: Salário mensal")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
          val = st.number_input(
              "Valor (R$)", min_value=0.00, format="%.2f", value=0.00
          )
        with col_v2:
          dt = st.date_input("Data", datetime.today())

        cat = st.selectbox("Categoria", CATEGORIAS_RECEITAS)
        obs = st.text_area(
            "Observações", placeholder="Adicione observações..."
        )
        rec = st.toggle("Recorrente")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
          salvar = st.form_submit_button(
              "Salvar Receita", use_container_width=True, type="primary"
          )
        with col_b2:
          fechar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
          if desc and val > 0:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO receitas (descricao, valor, data, categoria,"
                " observacoes, recorrente) VALUES (?, ?, ?, ?, ?, ?)",
                (desc, val, str(dt), cat, obs, 1 if rec else 0),
            )
            conn.commit()
            st.session_state["abrir_modal_receita"] = False
            st.success("Receita salva com sucesso!")
            st.rerun()
          else:
            st.warning(
                "Por favor, preencha a descrição e um valor maior que zero."
            )

        if fechar:
          st.session_state["abrir_modal_receita"] = False
          st.rerun()

      st.markdown("</div>", unsafe_allow_html=True)

  st.markdown(
      f"<p style='color: #6b7280; font-size: 12px;'>{qtd_receitas}"
      " receitas</p>",
      unsafe_allow_html=True,
  )

  if df_receitas.empty:
    st.markdown(
        """
        <div style='text-align: center; padding: 50px 20px; background-color: #161e2e; border: 1px solid #1f2937; border-radius: 12px; margin-top: 20px;'>
            <p style='color: #9ca3af; font-size: 15px; margin-bottom: 20px;'>Você ainda não tem receitas cadastradas</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
  else:
    df_filtrado = df_receitas.copy()
    if busca_termo:
      df_filtrado = df_filtrado[
          df_filtrado["descricao"].str.contains(busca_termo, case=False, na=False)
      ]
    if filtro_cat != "Todas as categorias":
      df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_cat]

    df_filtrado["Ícone"] = df_filtrado["categoria"].apply(obter_icone_receita)
    st.dataframe(
        df_filtrado[[
            "data",
            "Ícone",
            "descricao",
            "categoria",
            "valor",
            "observacoes",
        ]],
        use_container_width=True,
    )

# ==========================================
# MÓDULO: DESPESAS
# ==========================================
elif menu == "Despesas":
  c_t1, c_t2, c_t3 = st.columns([2, 2, 1])
  with c_t1:
    st.markdown(
        "<h1 style='margin-bottom: 0;'>Despesas</h1>", unsafe_allow_html=True
    )

  df_despesas = pd.read_sql("SELECT * FROM despesas", conn)
  total_geral_despesas = (
      df_despesas["valor"].sum() if not df_despesas.empty else 0.0
  )
  qtd_despesas = len(df_despesas)

  with c_t2:
    st.markdown(
        f"<p style='color: #9ca3af; margin-top: 10px;'>Total: <b style='color:"
        f" #f9fafb;'>R$ {total_geral_despesas:,.2f}</b></p>",
        unsafe_allow_html=True,
    )

  with c_t3:
    nova_desp_btn = st.button(
        "➕ Nova", use_container_width=True, type="primary"
    )

  # Barra de Filtros
  st.markdown('<div class="gm-card" style="padding: 15px;">', unsafe_allow_html=True)
  f1, f2 = st.columns(2)
  with f1:
    busca_termo = st.text_input(
        "Busca", placeholder="🔍 Buscar despesa...", label_visibility="collapsed"
    )
  with f2:
    filtro_cat = st.selectbox(
        "Categoria",
        ["Todas as categorias"] + CATEGORIAS_DESPESAS,
        label_visibility="collapsed",
    )
  st.markdown("</div>", unsafe_allow_html=True)

  # Painel de Cadastro de Nova Despesa
  if nova_desp_btn or st.session_state.get("abrir_modal_despesa", False):
    st.session_state["abrir_modal_despesa"] = True

    with st.container():
      st.markdown(
          """
            <div style='background-color: #161e2e; border: 1px solid #374151; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);'>
                <h3 style='margin-top: 0; color: #fff;'>Nova Despesa</h3>
            """,
          unsafe_allow_html=True,
      )

      with st.form("form_nova_despesa", clear_on_submit=True):
        desc = st.text_input("Descrição", placeholder="Ex: Conta de luz")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
          val = st.number_input(
              "Valor (R$)", min_value=0.00, format="%.2f", value=0.00
          )
        with col_v2:
          dt = st.date_input("Data", datetime.today())

        cat = st.selectbox("Categoria", CATEGORIAS_DESPESAS)
        obs = st.text_area(
            "Observações", placeholder="Adicione observações..."
        )
        rec = st.toggle("Recorrente")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
          salvar = st.form_submit_button(
              "Salvar Despesa", use_container_width=True, type="primary"
          )
        with col_b2:
          fechar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
          if desc and val > 0:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO despesas (descricao, valor, data, categoria,"
                " observacoes, recorrente) VALUES (?, ?, ?, ?, ?, ?)",
                (desc, val, str(dt), cat, obs, 1 if rec else 0),
            )
            conn.commit()
            st.session_state["abrir_modal_despesa"] = False
            st.success("Despesa salva com sucesso!")
            st.rerun()
          else:
            st.warning(
                "Por favor, preencha a descrição e um valor maior que zero."
            )

        if fechar:
          st.session_state["abrir_modal_despesa"] = False
          st.rerun()

      st.markdown("</div>", unsafe_allow_html=True)

  st.markdown(
      f"<p style='color: #6b7280; font-size: 12px;'>{qtd_despesas}"
      " despesas</p>",
      unsafe_allow_html=True,
  )

  if df_despesas.empty:
    st.markdown(
        """
        <div style='text-align: center; padding: 50px 20px; background-color: #161e2e; border: 1px solid #1f2937; border-radius: 12px; margin-top: 20px;'>
            <p style='color: #9ca3af; font-size: 15px; margin-bottom: 20px;'>Você ainda não tem despesas cadastradas</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
  else:
    df_filtrado = df_despesas.copy()
    if busca_termo:
      df_filtrado = df_filtrado[
          df_filtrado["descricao"].str.contains(busca_termo, case=False, na=False)
      ]
    if filtro_cat != "Todas as categorias":
      df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_cat]

    df_filtrado["Ícone"] = df_filtrado["categoria"].apply(obter_icone_despesa)
    st.dataframe(
        df_filtrado[[
            "data",
            "Ícone",
            "descricao",
            "categoria",
            "valor",
            "observacoes",
        ]],
        use_container_width=True,
    )

conn.close()
