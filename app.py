from datetime import datetime
import os
import sqlite3
import pandas as pd
import pdfplumber
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA (ESTILO GESTORMONEY)
# ==========================================
st.set_page_config(
    page_title="GestorMoney - Seu Aliado Financeiro",
    page_icon="💰",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color: #0c101d; color: #e5e7eb; }
    .stSidebar { background-color: #121826; border-right: 1px solid #1f2937; }
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
            observacoes TEXT,
            recorrente TEXT,
            origem TEXT
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
# MENU LATERAL (ESTILO GESTORMONEY)
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
        "Patrimônio 'Conta'",
        "Receitas",
        "Despesas",
        "Transações",
        "Cartões de Crédito",
        "Investimentos",
        "Importador Extratos (PDF)",
        "Regras De/Para",
        "Central de Backup",
    ],
)

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

  df_trans = pd.read_sql("SELECT * FROM transacoes", conn)
  df_inv = pd.read_sql("SELECT * FROM investimentos", conn)

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

  total_investido = (
      df_inv["total_investido"].sum() if not df_inv.empty else 0.0
  )
  valor_mercado = df_inv["valor_mercado"].sum() if not df_inv.empty else 0.0
  lucro_inv = valor_mercado - total_investido

  col_c1, col_c2 = st.columns(2)
  with col_c1:
    st.markdown(
        f"""
        <div class="gm-card">
            <span class="gm-card-title">💰 Disponível em Caixa</span>
            <div class="gm-card-value" style="color: #10b981;">R$ {disponivel_caixa:,.2f}</div>
            <div class="gm-card-footer">Inicial + saldo (sem investimentos)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with col_c2:
    st.markdown(
        f"""
        <div class="gm-card">
            <span class="gm-card-title">📈 Investimentos</span>
            <div style='display: flex; justify-content: space-between; margin-top: 15px;'>
                <div><span style='color: #6b7280; font-size: 11px;'>Total</span><br><b>R$ {total_investido:,.2f}</b></div>
                <div><span style='color: #6b7280; font-size: 11px;'>Mercado</span><br><b>R$ {valor_mercado:,.2f}</b></div>
                <div><span style='color: #6b7280; font-size: 11px;'>Lucro</span><br><b style='color: #10b981;'>+R$ {lucro_inv:,.2f}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# MÓDULO: PATRIMÔNIO "CONTA"
# ==========================================
elif menu == "Patrimônio 'Conta'":
  st.title("🏦 Patrimônio / Contas")
  st.info(
      "Gerencie suas contas bancárias, saldos iniciais e patrimônio consolidado."
  )
  df_trans = pd.read_sql("SELECT * FROM transacoes", conn)
  total_rec = (
      df_trans[df_trans["tipo"] == "Receita"]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  total_desp = (
      df_trans[df_trans["tipo"] == "Despesa"]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  st.metric("Saldo Consolidado em Contas", f"R$ {total_rec - total_desp:,.2f}")

# ==========================================
# MÓDULO: RECEITAS (Idêntico ao print)
# ==========================================
elif menu == "Receitas":
  st.title("Receitas")
  df_rec = (
      pd.read_sql(
          "SELECT * FROM transacoes WHERE tipo = 'Receita' ORDER BY data DESC",
          conn,
      )
      if not conn.cursor().execute(
          "SELECT name FROM sqlite_master WHERE name='transacoes'"
      ).fetchall()
      else pd.read_sql(
          "SELECT * FROM transacoes WHERE tipo = 'Receita' ORDER BY data DESC",
          conn,
      )
  )
  total_receita_geral = df_rec["valor"].sum() if not df_rec.empty else 0.0
  st.markdown(
      f"<p style='color: #9ca3af;'>Total: R$ {total_receita_geral:,.2f}</p>",
      unsafe_allow_html=True,
  )

  # Botões Superiores idênticos ao print (Simples, Recorrentes, Avançada, + Nova)
  b1, b2, b3, b4 = st.columns([1, 1, 1, 2])
  with b1:
    st.button("📋 Simples", use_container_width=True)
  with b2:
    st.button("🔄 Recorrentes", use_container_width=True)
  with b3:
    st.button("📊 Avançada", use_container_width=True)

  # Formulário flutuante estilo Modal idêntico à imagem
  with st.expander("➕ Adicionar Nova Receita", expanded=True):
    with st.form("form_nova_receita"):
      st.markdown("### Nova Receita")
      descricao = st.text_input(
          "Descrição", placeholder="Ex: Salário", key="desc_rec"
      )

      col_v, col_d = st.columns(2)
      with col_v:
        valor = st.number_input("Valor", min_value=0.01, format="%.2f")
      with col_d:
        data = st.date_input("Data", datetime.today())

      categoria = st.selectbox(
          "Categoria", list(ICONES_CATEGORIAS.keys()), key="cat_rec"
      )
      observacoes = st.text_area(
          "Observações",
          placeholder="Adicione observações...",
          key="obs_rec",
      )
      recorrente = st.toggle("Recorrente", key="rec_toggle")

      submitted = st.form_submit_button(
          "Salvar Receita", use_container_width=True
      )
      if submitted and descricao:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transacoes (data, descricao, valor, tipo, categoria,"
            " observacoes, recorrente, origem) VALUES (?, ?, ?, 'Receita', ?,"
            " ?, ?, ?)",
            (
                str(data),
                descricao,
                valor,
                categoria,
                observacoes,
                "Sim" if recorrente else "Não",
                "Conta Corrente",
            ),
        )
        conn.commit()
        st.success("Receita salva com sucesso!")
        st.rerun()

  st.subheader("Lista de Receitas")
  if not df_rec.empty:
    df_rec["Ícone"] = df_rec["categoria"].apply(obter_icone)
    st.dataframe(
        df_rec[
            [
                "data",
                "Ícone",
                "descricao",
                "categoria",
                "valor",
                "observacoes",
                "recorrente",
            ]
        ],
        use_container_width=True,
    )
  else:
    st.info("Você ainda não tem receitas cadastradas.")

# ==========================================
# MÓDULO: DESPESAS
# ==========================================
elif menu == "Despesas":
  st.title("Despesas")
  df_desp = pd.read_sql(
      "SELECT * FROM transacoes WHERE tipo = 'Despesa' ORDER BY data DESC", conn
  )
  total_desp_geral = df_desp["valor"].sum() if not df_desp.empty else 0.0
  st.markdown(
      f"<p style='color: #9ca3af;'>Total: R$ {total_desp_geral:,.2f}</p>",
      unsafe_allow_html=True,
  )

  with st.expander("➕ Adicionar Nova Despesa", expanded=True):
    with st.form("form_nova_despesa"):
      st.markdown("### Nova Despesa")
      descricao = st.text_input(
          "Descrição", placeholder="Ex: Supermercado", key="desc_desp"
      )

      col_v, col_d = st.columns(2)
      with col_v:
        valor = st.number_input("Valor", min_value=0.01, format="%.2f")
      with col_d:
        data = st.date_input("Data", datetime.today())

      categoria = st.selectbox(
          "Categoria", list(ICONES_CATEGORIAS.keys()), key="cat_desp"
      )
      observacoes = st.text_area(
          "Observações",
          placeholder="Adicione observações...",
          key="obs_desp",
      )
      recorrente = st.toggle("Recorrente", key="rec_toggle_desp")

      submitted = st.form_submit_button(
          "Salvar Despesa", use_container_width=True
      )
      if submitted and descricao:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transacoes (data, descricao, valor, tipo, categoria,"
            " observacoes, recorrente, origem) VALUES (?, ?, ?, 'Despesa', ?,"
            " ?, ?, ?)",
            (
                str(data),
                descricao,
                valor,
                categoria,
                observacoes,
                "Sim" if recorrente else "Não",
                "Cartão/Conta",
            ),
        )
        conn.commit()
        st.success("Despesa salva com sucesso!")
        st.rerun()

  st.subheader("Lista de Despesas")
  if not df_desp.empty:
    df_desp["Ícone"] = df_desp["categoria"].apply(obter_icone)
    st.dataframe(
        df_desp[
            [
                "data",
                "Ícone",
                "descricao",
                "categoria",
                "valor",
                "observacoes",
                "recorrente",
            ]
        ],
        use_container_width=True,
    )
  else:
    st.info("Você ainda não tem despesas cadastradas.")

# ==========================================
# MÓDULO: TRANSAÇÕES GERAIS
# ==========================================
elif menu == "Transações":
  st.title("🔄 Todas as Transações")
  df_all = pd.read_sql("SELECT * FROM transacoes ORDER BY data DESC", conn)
  if not df_all.empty:
    df_all["Ícone"] = df_all["categoria"].apply(obter_icone)
    st.dataframe(
        df_all[
            [
                "data",
                "Ícone",
                "descricao",
                "tipo",
                "categoria",
                "valor",
                "origem",
            ]
        ],
        use_container_width=True,
    )
  else:
    st.info("Nenhuma transação registrada.")

# ==========================================
# MÓDULO: CARTÕES DE CRÉDITO
# ==========================================
elif menu == "Cartões de Crédito":
  st.title("💳 Cartões de Crédito")
  st.info("Gerenciamento de faturas e limites de cartões.")

# ==========================================
# MÓDULO: INVESTIMENTOS
# ==========================================
elif menu == "Investimentos":
  st.title("📈 Controle de Investimentos")
  with st.form("form_inv"):
    ativo = st.text_input("Nome do Ativo (Ex: PETR4)")
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
  pdf_file = st.file_uploader(
      "Selecione o Extrato em PDF", type=["pdf"], key="pdf_up"
  )
  if pdf_file is not None:
    if st.button("Processar Extrato"):
      with pdfplumber.open(pdf_file) as pdf:
        texto = "".join([pagina.extract_text() for pagina in pdf.pages])
      st.text_area("Texto Extraído do PDF", texto, height=200)
      st.success("Extrato processado com sucesso!")

# ==========================================
# MÓDULO: REGRAS DE/PARA
# ==========================================
elif menu == "Regras De/Para":
  st.title("⚙️ Gerenciamento de Regras De/Para")
  with st.form("form_regras"):
    termo = st.text_input("Termo Chave (Ex: UBER, PADARIA)").upper()
    cat_atribuida = st.selectbox(
        "Categoria Correspondente", list(ICONES_CATEGORIAS.keys())
    )
    if st.form_submit_button("Salvar Regra") and termo:
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO regras_depara (termo_chave, categoria) VALUES (?, ?)",
          (termo, cat_atribuida),
      )
      conn.commit()
      st.success(f"Regra para '{termo}' salva!")
      st.rerun()

  df_regras = pd.read_sql("SELECT * FROM regras_depara", conn)
  if not df_regras.empty:
    st.dataframe(df_regras, use_container_width=True)

# ==========================================
# MÓDULO: CENTRAL DE BACKUP
# ==========================================
elif menu == "Central de Backup":
  st.title("💾 Central de Backup")
  if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
      st.download_button(
          label="📥 Baixar Backup Completo (.db)",
          data=f,
          file_name="gestormoney_backup.db",
          mime="application/octet-stream",
      )

conn.close()
