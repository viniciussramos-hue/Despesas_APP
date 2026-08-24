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


def obter_icone(categoria):
  icones = {
      "Alimentação": "🍔",
      "Supermercado": "🛒",
      "Moradia": "🏠",
      "Transporte": "🚗",
      "Combustível": "⛽",
      "Saúde": "💊",
      "Lazer": "🎮",
      "Serviços": "💡",
      "Salário": "💵",
      "Freelance": "💻",
      "Investimentos": "📈",
      "Vendas": "🏷️",
      "Reembolso": "🔄",
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
            <div class="gm-card-footer">Total cadastrado</div>
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
            <div class="gm-card-footer">Total cadastrado</div>
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


# ==========================================
# FUNÇÃO REUTILIZÁVEL PARA MÓDULOS (COM ABA AVANÇADA IDÊNTICA AO PRINT)
# ==========================================
def renderizar_modulo_financeiro(
    titulo, tabela, categorias, icone_func, cor_botao_novo
):
  c_t1, c_t2, c_t3 = st.columns([2, 2, 1])
  with c_t1:
    st.markdown(
        f"<h1 style='margin-bottom: 0;'>{titulo}</h1>", unsafe_allow_html=True
    )

  df_dados = pd.read_sql(f"SELECT * FROM {tabela}", conn)
  total_geral = df_dados["valor"].sum() if not df_dados.empty else 0.0
  qtd_registros = len(df_dados)

  with c_t2:
    st.markdown(
        f"<p style='color: #9ca3af; margin-top: 10px;'>Total: <b style='color:"
        f" #f9fafb;'>R$ {total_geral:,.2f}</b></p>",
        unsafe_allow_html=True,
    )

  with c_t3:
    nova_btn = st.button(
        "＋ Nova",
        use_container_width=True,
        type="primary" if cor_botao_novo == "primary" else "secondary",
    )

  # Sistema de Abas Superiores (Simples, Recorrentes, Avançada)
  aba = st.radio(
      "Abas",
      ["📋 Simples", "🔄 Recorrentes", "📊 Avançada"],
      horizontal=True,
      label_visibility="collapsed",
  )

  st.markdown("<br>", unsafe_allow_html=True)

  # Painel de Cadastro (Modal simulado)
  if nova_btn or st.session_state.get(f"abrir_modal_{tabela}", False):
    st.session_state[f"abrir_modal_{tabela}"] = True

    with st.container():
      st.markdown(
          f"""
            <div style='background-color: #161e2e; border: 1px solid #374151; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);'>
                <h3 style='margin-top: 0; color: #fff;'>Nova {titulo[:-1]}</h3>
            """,
          unsafe_allow_html=True,
      )

      with st.form(f"form_novo_{tabela}", clear_on_submit=True):
        desc = st.text_input("Descrição", placeholder="Ex: Conta / Salário")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
          val = st.number_input(
              "Valor (R$)", min_value=0.00, format="%.2f", value=0.00
          )
        with col_v2:
          dt = st.date_input("Data", datetime.today())

        cat = st.selectbox("Categoria", categorias)
        obs = st.text_area(
            "Observações", placeholder="Adicione observações..."
        )
        rec = st.toggle("Recorrente")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
          salvar = st.form_submit_button(
              f"Salvar {titulo[:-1]}", use_container_width=True, type="primary"
          )
        with col_b2:
          fechar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
          if desc and val > 0:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {tabela} (descricao, valor, data, categoria,"
                " observacoes, recorrente) VALUES (?, ?, ?, ?, ?, ?)",
                (desc, val, str(dt), cat, obs, 1 if rec else 0),
            )
            conn.commit()
            st.session_state[f"abrir_modal_{tabela}"] = False
            st.success(f"{titulo[:-1]} salva com sucesso!")
            st.rerun()
          else:
            st.warning(
                "Por favor, preencha a descrição e um valor maior que zero."
            )

        if fechar:
          st.session_state[f"abrir_modal_{tabela}"] = False
          st.rerun()

      st.markdown("</div>", unsafe_allow_html=True)

  # ==========================================
  # RENDERIZAÇÃO DA ABA AVANÇADA (IDÊNTICA AOS PRINTS)
  # ==========================================
  if aba == "📊 Avançada":
    # 1. Barra de Período Superior do Avançado
    st.markdown(
        """
        <div class="gm-card" style="padding: 15px; margin-bottom: 20px;">
            <span style="color: #9ca3af; font-size: 13px; font-weight: 500;">🔻 Período</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    p1, p2, p3 = st.columns([2, 2, 1])
    with p1:
      data_inicio = st.date_input(
          "Início", value=date(2026, 8, 1), key=f"ini_{tabela}"
      )
    with p2:
      data_fim = st.date_input(
          "Fim", value=date(2026, 8, 31), key=f"fim_{tabela}"
      )
    with p3:
      st.markdown("<br>", unsafe_allow_html=True)
      st.button("Filtrar", use_container_width=True, type="primary")

    # 2. Cards de Resumo Superior do Avançado
    if not df_dados.empty:
      df_dados["dt_obj"] = pd.to_datetime(
          df_dados["data"], errors="coerce"
      ).dt.date
      df_periodo = df_dados[
          (df_dados["dt_obj"] >= data_inicio)
          & (df_dados["dt_obj"] <= data_fim)
      ]
    else:
      df_periodo = pd.DataFrame(columns=df_dados.columns)

    total_periodo = (
        df_periodo["valor"].sum() if not df_periodo.empty else 0.0
    )
    maior_valor = (
        df_periodo["valor"].max() if not df_periodo.empty else 0.0
    )

    ac1, ac2, ac3 = st.columns(3)
    if tabela == "despesas":
      with ac1:
        st.markdown(
            f"""
            <div class="gm-card" style="background-color: #181216; border: 1px solid #3b1f23;">
                <div class="gm-card-title">🏛️ DESPESAS GERAIS</div>
                <div class="gm-card-value" style="color: #ef4444;">R$ {total_periodo:,.2f}</div>
                <div class="gm-card-footer">Saídas da conta no período</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
      with ac2:
        st.markdown(
            """
            <div class="gm-card" style="background-color: #141624; border: 1px solid #23223b;">
                <div class="gm-card-title">💳 COMPRAS NO CARTÃO</div>
                <div class="gm-card-value" style="color: #a855f7;">R$ 0,00</div>
                <div class="gm-card-footer">Parcelas e compras à vista</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
      with ac3:
        st.markdown(
            f"""
            <div class="gm-card" style="background-color: #121f18; border: 1px solid #1f3b27;">
                <div class="gm-card-title">🛡️ TOTAL QUE VOCÊ GASTOU</div>
                <div class="gm-card-value" style="color: #10b981;">R$ {total_periodo:,.2f}</div>
                <div class="gm-card-footer">Conta + cartões no período</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
      with ac1:
        st.markdown(
            f"""
            <div class="gm-card" style="background-color: #121f18; border: 1px solid #1f3b27;">
                <div class="gm-card-title">💲 TOTAL DE RECEITAS</div>
                <div class="gm-card-value" style="color: #10b981;">R$ {total_periodo:,.2f}</div>
                <div class="gm-card-footer">Soma de todas as entradas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
      with ac2:
        st.markdown(
            f"""
            <div class="gm-card" style="background-color: #141624; border: 1px solid #23223b;">
                <div class="gm-card-title">📊 MÉDIA MENSAL</div>
                <div class="gm-card-value" style="color: #3b82f6;">R$ {total_periodo:,.2f}</div>
                <div class="gm-card-footer">Baseado no período</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
      with ac3:
        st.markdown(
            f"""
            <div class="gm-card" style="background-color: #181216; border: 1px solid #3b1f23;">
                <div class="gm-card-title">🏆 MAIOR {titulo[:-1].upper()}</div>
                <div class="gm-card-value" style="color: #f59e0b;">R$ {maior_valor:,.2f}</div>
                <div class="gm-card-footer">Pico no período selecionado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Gráfico por Categoria (Estilo Card do Print)
    st.markdown(
        f"""
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <b>{titulo} por Categoria</b><br>
                    <span style="color: #6b7280; font-size: 11px;">{data_inicio.strftime('%d/%m')} - {data_fim.strftime('%d/%m')} • Total: R$ {total_periodo:,.2f}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df_periodo.empty:
      df_cat = df_periodo.groupby("categoria")["valor"].sum().reset_index()
      st.bar_chart(df_cat.set_index("categoria"))
    else:
      st.markdown(
          "<p style='text-align: center; color: #6b7280; padding: 20px;'>Nenhuma"
          " categoria no período.</p>",
          unsafe_allow_html=True,
      )

    # 4. Ranking das Maiores Movimentações
    st.markdown(
        f"""
        <div class="gm-card">
            <b>Ranking das Maiores {titulo}</b><br>
            <span style="color: #6b7280; font-size: 11px;">{data_inicio.strftime('%d/%m')} - {data_fim.strftime('%d/%m')} • {len(df_periodo)} registros</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df_periodo.empty:
      df_ranking = df_periodo.sort_values(by="valor", ascending=False)
      df_ranking["Ícone"] = df_ranking["categoria"].apply(icone_func)
      st.dataframe(
          df_ranking[[
              "data",
              "Ícone",
              "descricao",
              "categoria",
              "valor",
              "observacoes",
          ]],
          use_container_width=True,
      )
    else:
      st.markdown(
          "<p style='text-align: center; color: #6b7280; padding: 20px;'>Nenhum"
          " registro no período.</p>",
          unsafe_allow_html=True,
      )

  # ==========================================
  # RENDERIZAÇÃO DAS ABAS SIMPLES / RECORRENTES
  # ==========================================
  else:
    st.markdown(
        '<div class="gm-card" style="padding: 15px;">', unsafe_allow_html=True
    )
    f1, f2, f3, f4 = st.columns(4)
    with f1:
      busca = st.text_input(
          "Busca",
          placeholder=f"🔍 Buscar {titulo.lower()}...",
          label_visibility="collapsed",
      )
    with f2:
      filtro_cat = st.selectbox(
          "Categoria",
          ["Todas as categorias"] + categorias,
          label_visibility="collapsed",
      )
    with f3:
      st.selectbox(
          "Membros",
          ["Todos os membros", "Vinicius Ramos"],
          label_visibility="collapsed",
      )
    with f4:
      st.selectbox(
          "Status", ["Todas", "Pagas", "Pendentes"], label_visibility="collapsed"
      )
    st.markdown("</div>", unsafe_allow_html=True)

    df_filtrado = df_dados.copy()
    if not df_filtrado.empty:
      if aba == "🔄 Recorrentes":
        df_filtrado = df_filtrado[df_filtrado["recorrente"] == 1]
      if busca:
        df_filtrado = df_filtrado[
            df_filtrado["descricao"].str.contains(busca, case=False, na=False)
        ]
      if filtro_cat != "Todas as categorias":
        df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_cat]

    st.markdown(
        f"<p style='color: #6b7280; font-size: 12px;'>{qtd_registros}"
        f" {titulo.lower()}</p>",
        unsafe_allow_html=True,
    )

    if df_dados.empty:
      st.markdown(
          f"""
            <div style='text-align: center; padding: 50px 20px; background-color: #161e2e; border: 1px solid #1f2937; border-radius: 12px; margin-top: 20px;'>
                <p style='color: #9ca3af; font-size: 15px; margin-bottom: 20px;'>Você ainda não tem {titulo.lower()} cadastradas</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    else:
      df_filtrado["Ícone"] = df_filtrado["categoria"].apply(icone_func)
      st.dataframe(
          df_filtrado[[
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
      with st.expander(f"🗑️ Excluir {titulo[:-1]} por ID"):
        id_exc = st.number_input(
            f"ID da {titulo[:-1]} para remover",
            min_value=1,
            step=1,
            format="%d",
            key=f"exc_{tabela}",
        )
        if st.button(
            "Remover Registro", type="primary", key=f"btn_exc_{tabela}"
        ):
          cursor = conn.cursor()
          cursor.execute(f"DELETE FROM {tabela} WHERE id = ?", (id_exc,))
          conn.commit()
          st.success("Registro excluído com sucesso!")
          st.rerun()


# ==========================================
# ROTEAMENTO DOS MÓDULOS ATIVOS
# ==========================================
if menu == "Receitas":
  renderizar_modulo_financeiro(
      "Receitas",
      "receitas",
      CATEGORIAS_RECEITAS,
      lambda c: obter_icone(c),
      "primary",
  )

elif menu == "Despesas":
  renderizar_modulo_financeiro(
      "Despesas",
      "despesas",
      CATEGORIAS_DESPESAS,
      lambda c: obter_icone(c),
      "primary",
  )

conn.close()
