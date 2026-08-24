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

  conn.commit()
  conn.close()


init_db()

CATEGORIAS_DESPESAS = [
    "Alimentação",
    "Aluguel",
    "Combustível",
    "Lazer",
    "Saúde",
    "Outros",
]
CATEGORIAS_RECEITAS = ["Salário", "Freelance", "Investimentos", "Outros"]


def obter_icone(categoria):
  icones = {
      "Alimentação": "🍔",
      "Aluguel": "🏠",
      "Combustível": "⛽",
      "Lazer": "🎮",
      "Saúde": "💊",
      "Salário": "💵",
      "Freelance": "💻",
      "Investimentos": "📈",
      "Outros": "📦",
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

if st.sidebar.button(
    "🔄 Transações",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Transações"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Transações"
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
# MÓDULO: DASHBOARD (FIEL ÀS REFERÊNCIAS)
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

  # Barra de Conquistas / Troféus
  st.markdown(
      """
      <div style='background-color: #161e2e; border: 1px solid #1f2937; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; font-size: 14px;'>
          <span style='color: #f59e0b; font-weight: bold;'>🏆 0/9</span>
          <span style='color: #6b7280;'>|</span>
          <span>🎯 🪙 🛡️ 📊 💡 🚀 👑 ⚡ ❓</span>
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

  # --- PRIMEIRA LINHA DE CARDS ---
  col_c1, col_c2 = st.columns(2)
  with col_c1:
    st.markdown(
        f"""
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="gm-card-title">💰 Disponível em Caixa ℹ️</span>
                <span style="color: #10b981; font-size: 16px;">👁️</span>
            </div>
            <div class="gm-card-value" style="color: #10b981;">R$ {saldo_caixa:,.2f}</div>
            <div class="gm-card-footer">Patrimônio inicial<br>Saldo (receitas – despesas): R$ {saldo_caixa:,.2f}</div>
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
                <span class="gm-card-title">📈 Investimentos ℹ️</span>
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

  # --- SEGUNDA LINHA DE CARDS ---
  dc1, dc2, dc3, dc4 = st.columns(4)
  with dc1:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">📉 Dívida Total ℹ️</div>
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
            <div class="gm-card-title">↗️ Contas a Receber Este Mês ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">R$ {total_receitas:,.2f}</div>
            <div class="gm-card-footer">Vencimentos do mês</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc3:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">📅 Contas a Pagar Este Mês ℹ️</div>
            <div class="gm-card-value" style="color: #f59e0b;">R$ {total_despesas:,.2f}</div>
            <div class="gm-card-footer">Cartões + contas + dívidas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc4:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">💳 Limite Disponível Cartões ℹ️</div>
            <div class="gm-card-value" style="color: #3b82f6;">R$ 0,00</div>
            <div class="gm-card-footer">Limite total: R$ 0,00</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.divider()

  # --- GRÁFICOS INFERIORES ---
  gc1, gc2 = st.columns(2)
  with gc1:
    st.subheader("Fluxo de Caixa Pessoal")
    st.markdown(
        "<p style='color: #6b7280; font-size: 12px;'>Movimentação financeira"
        " dos últimos 6 meses</p>",
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
        "<p style='color: #6b7280; font-size: 12px;'>Receitas vs Despesas -"
        " Semana atual (Dom a Sáb)</p>",
        unsafe_allow_html=True,
    )
    if not df_desp.empty or not df_rec.empty:
      st.line_chart(chart_data)
    else:
      st.info("Sem dados suficientes para o comparativo semanal.")

  st.divider()

  # --- SELETOR DE PERÍODO ---
  st.markdown("### Período de Análise")
  st.markdown(
      "<p style='color: #6b7280; font-size: 12px;'>Selecione o período para"
      " visualizar as estatísticas</p>",
      unsafe_allow_html=True,
  )
  periodo_sel = st.selectbox(
      "Período",
      ["Mês Atual", "Últimos 3 Meses", "Ano Atual", "Personalizado"],
      label_visibility="collapsed",
  )

  # --- CARDS DO PERÍODO SELECIONADO ---
  pc1, pc2, pc3, pc4 = st.columns(4)
  with pc1:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">Saldo do Período ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">R$ {saldo_caixa:,.2f}</div>
            <div class="gm-card-footer">Receitas - Despesas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with pc2:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">Receitas ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">R$ {total_receitas:,.2f}</div>
            <div class="gm-card-footer">No período selecionado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with pc3:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">Despesas ℹ️</div>
            <div class="gm-card-value" style="color: #ef4444;">R$ {total_despesas:,.2f}</div>
            <div class="gm-card-footer">No período selecionado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with pc4:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">Saúde Financeira ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">0.0%</div>
            <div class="gm-card-footer" style="color: #10b981;">❤ Excelente</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  # --- SEÇÕES INFERIORES: ORIGEM/DESTINO E MEMBROS ---
  inf1, inf2 = st.columns(2)
  with inf1:
    st.markdown(
        """
        <div class="gm-card">
            <b>Origem das Receitas</b><br>
            <span style="color: #6b7280; font-size: 11px;">Distribuição por categoria</span>
            <div style="text-align: center; padding: 40px; color: #6b7280;">Nenhuma receita no período selecionado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with inf2:
    st.markdown(
        """
        <div class="gm-card">
            <b>Destino das Despesas</b><br>
            <span style="color: #6b7280; font-size: 11px;">Consolidado: transações gerais + cartão de crédito</span>
            <div style="text-align: center; padding: 40px; color: #6b7280;">Nenhuma despesa no período selecionado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  # Transações recentes e Membros
  t_col1, t_col2 = st.columns([2, 1])
  with t_col1:
    st.markdown(
        """
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b>Transações Recentes</b>
                <span style="color: #3b82f6; font-size: 12px; cursor: pointer;">Ver todas</span>
            </div>
            <div style="text-align: center; padding: 60px; color: #6b7280;">Nenhuma transação recente</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with t_col2:
    st.markdown(
        f"""
        <div class="gm-card">
            <b>Resumo por Membro</b><br>
            <span style="color: #6b7280; font-size: 11px;">Despesas e receitas no período</span>
            
            <div style="background-color: #121826; padding: 10px; border-radius: 8px; margin-top: 15px;">
                <span style="background: #f59e0b; color: #000; padding: 2px 6px; border-radius: 50%; font-size: 10px; font-weight: bold;">VD</span>
                <b style="font-size: 13px; margin-left: 5px;">Vinicius Da Silva Ramos</b>
                <div style="background: #10b98122; color: #10b981; padding: 4px; border-radius: 4px; font-size: 12px; margin-top: 8px; display: flex; justify-content: space-between;">
                    <span>Receitas:</span> <b>R$ {total_receitas:,.2f}</b>
                </div>
                <div style="background: #ef444422; color: #ef4444; padding: 4px; border-radius: 4px; font-size: 12px; margin-top: 5px; display: flex; justify-content: space-between;">
                    <span>Despesas:</span> <b>R$ {total_despesas:,.2f}</b>
                </div>
            </div>

            <div style="background-color: #121826; padding: 10px; border-radius: 8px; margin-top: 10px;">
                <span style="background: #8b5cf6; color: #fff; padding: 2px 6px; border-radius: 50%; font-size: 10px; font-weight: bold;">VR</span>
                <b style="font-size: 13px; margin-left: 5px;">Vanessa Rodrigues Ramos</b>
                <div style="background: #10b98122; color: #10b981; padding: 4px; border-radius: 4px; font-size: 12px; margin-top: 8px; display: flex; justify-content: space-between;">
                    <span>Receitas:</span> <b>R$ 0,00</b>
                </div>
                <div style="background: #ef444422; color: #ef4444; padding: 4px; border-radius: 4px; font-size: 12px; margin-top: 5px; display: flex; justify-content: space-between;">
                    <span>Despesas:</span> <b>R$ 0,00</b>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# OUTROS MÓDULOS (TRANSAÇÕES, CATEGORIAS, RECEITAS, DESPESAS)
# ==========================================
elif menu == "Transações":
  st.markdown("<h1>Transações</h1>", unsafe_allow_html=True)
  df_r = pd.read_sql("SELECT * FROM receitas", conn)
  if not df_r.empty:
    df_r["Tipo"] = "Receita"
  df_d = pd.read_sql("SELECT * FROM despesas", conn)
  if not df_d.empty:
    df_d["Tipo"] = "Despesa"
  df_transacoes = pd.concat([df_r, df_d], ignore_index=True)
  if not df_transacoes.empty:
    df_transacoes["Ícone"] = df_transacoes["categoria"].apply(obter_icone)
    st.dataframe(
        df_transacoes[[
            "id",
            "data",
            "Ícone",
            "descricao",
            "categoria",
            "Tipo",
            "valor",
            "observacoes",
        ]],
        use_container_width=True,
    )
  else:
    st.info("Nenhuma transação cadastrada.")

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

  if nova_cat_btn or st.session_state.get("abrir_modal_categoria", False):
    st.session_state["abrir_modal_categoria"] = True
    with st.container():
      st.markdown(
          """
            <div style='background-color: #161e2e; border: 1px solid #374151; padding: 25px; border-radius: 12px; margin-bottom: 25px;'>
                <h3 style='margin-top: 0; color: #fff;'>Nova Categoria</h3>
            """,
          unsafe_allow_html=True,
      )
      with st.form("form_nova_categoria", clear_on_submit=True):
        nome_cat = st.text_input("Nome da Categoria")
        tipo_cat = st.selectbox("Tipo", ["Despesa", "Receita"])
        icone_cat = st.text_input("Ícone (Emoji)", value="📁")
        b1, b2 = st.columns(2)
        with b1:
          salvar_cat = st.form_submit_button(
              "Salvar", use_container_width=True, type="primary"
          )
        with b2:
          fechar_cat = st.form_submit_button("Cancelar", use_container_width=True)
        if salvar_cat and nome_cat:
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO categorias (nome, tipo, icone) VALUES (?, ?, ?)",
              (nome_cat, tipo_cat, icone_cat),
          )
          conn.commit()
          st.session_state["abrir_modal_categoria"] = False
          st.rerun()
        if fechar_cat:
          st.session_state["abrir_modal_categoria"] = False
          st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

  df_categorias = pd.read_sql("SELECT * FROM categorias", conn)
  if df_categorias.empty:
    st.info("Nenhuma categoria encontrada.")
  else:
    for i in range(0, len(df_categorias), 4):
      subset = df_categorias.iloc[i : i + 4]
      cols = st.columns(4)
      for idx, (_, row) in enumerate(subset.iterrows()):
        with cols[idx]:
          cor = "#10b981" if row["tipo"] == "Receita" else "#ef4444"
          st.markdown(
              f"""
                <div class="gm-card" style="padding: 15px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{row['icone']}</span>
                        <span style="color: {cor}; font-size: 10px; font-weight: bold;">{row['tipo']}</span>
                    </div>
                    <div style="font-weight: bold; margin-top: 10px; color: #fff;">{row['nome']}</div>
                </div>
                """,
              unsafe_allow_html=True,
          )

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
        desc = st.text_input("Descrição")
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
    df_dados["Ícone"] = df_dados["categoria"].apply(obter_icone)
    st.dataframe(
        df_dados[[
            "id",
            "data",
            "Ícone",
            "descricao",
            "categoria",
            "valor",
            "observacoes",
        ]],
        use_container_width=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(f"🗑️ Excluir / Corrigir {titulo[:-1]} Lançada Errada"):
      id_deletar = st.number_input(
          f"Informe o ID da {titulo[:-1].lower()} que deseja excluir",
          min_value=1,
          step=1,
          format="%d",
          key=f"del_id_{tabela}",
      )
      if st.button(
          f"Confirmar Exclusão de {titulo[:-1]}",
          type="primary",
          key=f"btn_del_{tabela}",
      ):
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {tabela} WHERE id = ?", (id_deletar,))
        conn.commit()
        st.success(
            f"{titulo[:-1]} com ID {id_deletar} foi excluída com sucesso!"
        )
        st.rerun()
  else:
    st.info(f"Nenhuma {titulo.lower()} cadastrada.")

conn.close()
