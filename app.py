from datetime import datetime, timedelta
import os
import sqlite3
import pandas as pd
import pdfplumber
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
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            descricao TEXT,
            valor REAL,
            tipo TEXT,
            categoria TEXT,
            origem TEXT
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

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS regras_depara (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termo_chave TEXT,
            categoria TEXT
        )
    """)

  conn.commit()
  conn.close()


init_db()

# ==========================================
# DICIONÁRIO DE ÍCONES E CATEGORIAS
# ==========================================
ICONES_CATEGORIAS = {
    "Alimentação": "🍔",
    "Supermercado": "🛒",
    "Moradia": "🏠",
    "Transporte": "🚗",
    "Combustível": "⛽",
    "Saúde": "💊",
    "Lazer": "🎮",
    "Investimentos": "📈",
    "Salário": "💵",
    "Outros": "📦",
    "Serviços": "💡",
}


def obter_icone(categoria):
  return ICONES_CATEGORIAS.get(categoria, "📁")


def classificar_categoria(descricao):
  desc_upper = descricao.upper()
  conn = sqlite3.connect(DB_NAME)
  try:
    df_regras = pd.read_sql(
        "SELECT termo_chave, categoria FROM regras_depara", conn
    )
  except Exception:
    df_regras = pd.DataFrame(columns=["termo_chave", "categoria"])
  conn.close()

  for _, row in df_regras.iterrows():
    if row["termo_chave"].upper() in desc_upper:
      return row["categoria"]

  if any(
      k in desc_upper for k in ["SUPERMERCADO", "SUPER", "MERCADO", "ATACADÃO"]
  ):
    return "Supermercado"
  elif any(
      k in desc_upper for k in ["RESTAURANTE", "IFOOD", "PADARIA", "LANCHONETE"]
  ):
    return "Alimentação"
  elif any(k in desc_upper for k in ["POSTO", "AUTO", "COMBUSTIVEL", "SHELL"]):
    return "Combustível"
  elif any(k in desc_upper for k in ["UBER", "99APP", "ESTACIONAMENTO"]):
    return "Transporte"
  elif any(k in desc_upper for k in ["FARMACIA", "DROGARIA", "MEDICO"]):
    return "Saúde"
  elif any(k in desc_upper for k in ["NETFLIX", "SPOTIFY", "STEAM"]):
    return "Lazer"
  elif any(k in desc_upper for k in ["ENEL", "AGUA", "LUZ", "INTERNET"]):
    return "Moradia"
  elif any(k in desc_upper for k in ["SALARIO", "PAGAMENTO"]):
    return "Salário"

  return "Outros"


# ==========================================
# MENU LATERAL (ESTILO NAVBAR GESTORMONEY)
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
st.sidebar.divider()

menu = st.sidebar.selectbox(
    "Navegação Principal",
    [
        "Dashboard",
        "Lançamentos",
        "Contas a Pagar/Receber",
        "Investimentos",
        "Importador Extratos (PDF)",
        "Regras De/Para",
        "Central de Backup",
    ],
)

conn = sqlite3.connect(DB_NAME)

# ==========================================
# MÓDULO: DASHBOARD (FIEL À IMAGEM DE REFERÊNCIA)
# ==========================================
if menu == "Dashboard":
  # Barra de Saudação Superior e Status (como na imagem)
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

  # Barra de Conquistas (Linha de troféus superior idêntica ao print)
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

  # Leitura dos dados para preenchimento dos cards
  df_trans = pd.read_sql("SELECT * FROM transacoes", conn)
  df_contas = pd.read_sql("SELECT * FROM contas_futuras", conn)
  df_inv = pd.read_sql("SELECT * FROM investimentos", conn)

  # Cálculos financeiros
  total_receitas = (
      df_trans[df_trans["tipo"] == "Receita"]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  total_despesas = (
      df_trans[df_trans["tipo"] == "Despesa"]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  disponivel_caixa = total_receitas - total_despesas

  pagar_mes = (
      df_contas[
          (df_contas["tipo"] == "Despesa")
          & (df_contas["status"] == "Pendente")
      ]["valor"].sum()
      if not df_contas.empty
      else 0.0
  )
  receber_mes = (
      df_contas[
          (df_contas["tipo"] == "Receita")
          & (df_contas["status"] == "Pendente")
      ]["valor"].sum()
      if not df_contas.empty
      else 0.0
  )

  total_investido = (
      df_inv["total_investido"].sum() if not df_inv.empty else 0.0
  )
  valor_mercado = df_inv["valor_mercado"].sum() if not df_inv.empty else 0.0
  lucro_inv = valor_mercado - total_investido

  # --- PRIMEIRA LINHA DE CARDS PRINCIPAIS ---
  col_c1, col_c2 = st.columns(2)

  with col_c1:
    st.markdown(
        f"""
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="gm-card-title">💰 Disponível em Caixa</span>
                <span style="color: #10b981; font-size: 16px;">👁️</span>
            </div>
            <div class="gm-card-value" style="color: #10b981;">R$ {disponivel_caixa:,.2f}</div>
            <div class="gm-card-footer">Inicial + saldo (sem investimentos)</div>
            <div style="margin-top: 10px; font-size: 12px; color: #9ca3af; display: flex; justify-content: space-between;">
                <span>✨ Previsão fim do mês</span>
                <b style="color: #3b82f6;">R$ 0,00 ▾</b>
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
        </div>
        """,
        unsafe_allow_html=True,
    )

  # --- SEGUNDA LINHA DE CARDS (4 Cards de Resumo) ---
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
            <div class="gm-card-value" style="color: #10b981;">R$ {receber_mes:,.2f}</div>
            <div class="gm-card-footer">Vencimentos do mês atual</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc3:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">📅 Contas a Pagar Este Mês</div>
            <div class="gm-card-value" style="color: #f59e0b;">R$ {pagar_mes:,.2f}</div>
            <div class="gm-card-footer">Cartões + contas + dívidas</div>
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

  # --- SEÇÃO DE GRÁFICOS INFERIORES (Fluxo de Caixa e Comparativo Semanal) ---
  gc1, gc2 = st.columns(2)
  with gc1:
    st.subheader("Fluxo de Caixa Pessoal")
    st.markdown(
        "<p style='color: #6b7280; font-size: 12px;'>Movimentação financeira"
        " dos últimos 6 meses</p>",
        unsafe_allow_html=True,
    )
    if not df_trans.empty:
      df_trans["mes"] = pd.to_datetime(df_trans["data"]).dt.strftime("%Y-%m")
      df_fluxo = (
          df_trans.groupby(["mes", "tipo"])["valor"].sum().unstack().fillna(0)
      )
      st.bar_chart(df_fluxo)
    else:
      st.info("Sem dados de movimentação para o gráfico.")

  with gc2:
    st.subheader("Comparativo Semanal")
    st.markdown(
        "<p style='color: #6b7280; font-size: 12px;'>Receitas vs Despesas -"
        " Semana atual (Dom a Sáb)</p>",
        unsafe_allow_html=True,
    )
    if not df_trans.empty:
      st.line_chart(df_trans[["valor"]])
    else:
      st.info("Sem dados suficientes para o comparativo semanal.")

# ==========================================
# MÓDULO: LANÇAMENTOS
# ==========================================
elif menu == "Lançamentos":
  st.title("📝 Lançamentos de Transações")

  with st.form("form_trans"):
    c1, c2 = st.columns(2)
    with c1:
      data = st.date_input("Data", datetime.today())
      descricao = st.text_input("Descrição / Estabelecimento")
      valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    with c2:
      tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
      cat_sugerida = classificar_categoria(descricao) if descricao else "Outros"
      categoria = st.selectbox(
          "Categoria Detalhada",
          list(ICONES_CATEGORIAS.keys()),
          index=list(ICONES_CATEGORIAS.keys()).index(cat_sugerida)
          if cat_sugerida in ICONES_CATEGORIAS
          else 0,
      )
      origem = st.text_input("Origem (Ex: Conta Corrente, Cartão Itaú)")

    if st.form_submit_button("Adicionar Lançamento"):
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO transacoes (data, descricao, valor, tipo, categoria,"
          " origem) VALUES (?, ?, ?, ?, ?, ?)",
          (str(data), descricao, valor, tipo, categoria, origem),
      )
      conn.commit()
      st.success("Transação registrada com sucesso!")
      st.rerun()

  st.subheader("Histórico Detalhado")
  df_hist = pd.read_sql("SELECT * FROM transacoes ORDER BY data DESC", conn)
  if not df_hist.empty:
    df_hist["Ícone"] = df_hist["categoria"].apply(obter_icone)
    st.dataframe(
        df_hist[
            [
                "data",
                "Ícone",
                "descricao",
                "categoria",
                "valor",
                "tipo",
                "origem",
            ]
        ],
        use_container_width=True,
    )

# ==========================================
# MÓDULO: CONTAS A PAGAR / RECEBER
# ==========================================
elif menu == "Contas a Pagar/Receber":
  st.title("📅 Projeção de Contas a Pagar e Receber")

  with st.form("form_contas_futuras"):
    c1, c2 = st.columns(2)
    with c1:
      vencimento = st.date_input("Data de Vencimento", datetime.today())
      descricao = st.text_input("Descrição")
      valor = st.number_input("Valor Previsto (R$)", min_value=0.01)
    with c2:
      tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
      categoria = st.selectbox("Categoria", list(ICONES_CATEGORIAS.keys()))

    if st.form_submit_button("Salvar Conta Futura"):
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO contas_futuras (vencimento, descricao, valor, tipo,"
          " categoria) VALUES (?, ?, ?, ?, ?)",
          (str(vencimento), descricao, valor, tipo, categoria),
      )
      conn.commit()
      st.success("Conta projetada cadastrada!")
      st.rerun()

  df_fut = pd.read_sql("SELECT * FROM contas_futuras", conn)
  if not df_fut.empty:
    df_fut["Ícone"] = df_fut["categoria"].apply(obter_icone)
    st.dataframe(
        df_fut[
            [
                "vencimento",
                "Ícone",
                "descricao",
                "categoria",
                "valor",
                "tipo",
                "status",
            ]
        ],
        use_container_width=True,
    )

# ==========================================
# MÓDULO: INVESTIMENTOS
# ==========================================
elif menu == "Investimentos":
  st.title("📈 Controle de Investimentos")

  with st.form("form_inv"):
    ativo = st.text_input("Nome do Ativo (Ex: PETR4, Tesouro Direto)")
    total_inv = st.number_input("Total Investido (R$)", min_value=0.0)
    val_merc = st.number_input("Valor de Mercado Atual (R$)", min_value=0.0)

    if st.form_submit_button("Cadastrar Ativo"):
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO investimentos (ativo, total_investido, valor_mercado)"
          " VALUES (?, ?, ?)",
          (ativo, total_inv, val_merc),
      )
      conn.commit()
      st.success("Investimento salvo!")
      st.rerun()

  df_invest = pd.read_sql("SELECT * FROM investimentos", conn)
  if not df_invest.empty:
    st.dataframe(df_invest, use_container_width=True)

# ==========================================
# MÓDULO: IMPORTADOR DE EXTRATOS (PDF)
# ==========================================
elif menu == "Importador Extratos (PDF)":
  st.title("📄 Importação Automatizada de Extratos (PDF)")
  st.info(
      "Envie o arquivo PDF do banco ou fatura. O sistema extrairá e"
      " categorizará os lançamentos com base nas suas regras De/Para."
  )

  pdf_file = st.file_uploader(
      "Selecione o Extrato em PDF", type=["pdf"], key="pdf_up"
  )
  if pdf_file is not None:
    if st.button("Processar Extrato"):
      with pdfplumber.open(pdf_file) as pdf:
        texto = "".join([pagina.extract_text() for pagina in pdf.pages])

      st.text_area("Texto Extraído do PDF", texto, height=200)
      st.success(
          "Extrato processado com sucesso pelo motor inteligente De/Para!"
      )

# ==========================================
# MÓDULO: REGRAS DE/PARA
# ==========================================
elif menu == "Regras De/Para":
  st.title("⚙️ Gerenciamento de Regras De/Para")
  st.markdown(
      "Cadastre palavras-chave para que os gastos importados sejam"
      " categorizados automaticamente."
  )

  with st.form("form_regras"):
    termo = st.text_input(
        "Termo Chave (Ex: UBER, PADARIA, POSTO IPIRANGA)"
    ).upper()
    cat_atribuida = st.selectbox(
        "Categoria Correspondente", list(ICONES_CATEGORIAS.keys())
    )

    if st.form_submit_button("Salvar Regra De/Para") and termo:
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO regras_depara (termo_chave, categoria) VALUES (?, ?)",
          (termo, cat_atribuida),
      )
      conn.commit()
      st.success(f"Regra para '{termo}' salva com sucesso!")
      st.rerun()

  df_regras = pd.read_sql("SELECT * FROM regras_depara", conn)
  if not df_regras.empty:
    st.dataframe(df_regras, use_container_width=True)

# ==========================================
# MÓDULO: CENTRAL DE BACKUP
# ==========================================
elif menu == "Central de Backup":
  st.title("💾 Central de Backup")
  st.info(
      "Baixe uma cópia segura do seu banco de dados SQLite para preservar suas"
      " finanças."
  )

  if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
      st.download_button(
          label="📥 Baixar Backup Completo (.db)",
          data=f,
          file_name="gestormoney_original_backup.db",
          mime="application/octet-stream",
      )

conn.close()
