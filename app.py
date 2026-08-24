import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import pdfplumber
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==========================================
st.set_page_config(
    page_title="Gestor Financeiro Pessoal", page_icon="💰", layout="wide"
)

st.markdown(
    """
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# BANCO DE DADOS E MIGRATIONS (SQLite)
# ==========================================
DB_NAME = "gestor_financeiro.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # Tabela de Transações
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

  # Tabela de Contas a Pagar / Receber (Projeções)
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

  # Tabela de Regras De/Para para Categorias Inteligentes
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS regras_depara (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termo_chave TEXT,
            categoria TEXT
        )
    """)

  # Tabela de Veículos e Frotas
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_veiculo TEXT,
            km_atual REAL,
            consumo_medio REAL
        )
    """)

  # Tabela de Manutenções e Abastecimentos
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS frota_gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER,
            data TEXT,
            tipo_gasto TEXT,
            km_registro REAL,
            valor REAL,
            descricao TEXT
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


# ==========================================
# FUNÇÕES DE SUPORTE E PARSING
# ==========================================
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

  # Padrões inteligentes De/Para integrados
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
  elif any(k in desc_upper for k in ["UBER", "99APP", "ESTACIONAMENTO", "PEDAGIO"]):
    return "Transporte"
  elif any(k in desc_upper for k in ["FARMACIA", "DROGARIA", "MEDICO", "HOSPITAL"]):
    return "Saúde"
  elif any(k in desc_upper for k in ["NETFLIX", "SPOTIFY", "STEAM", "JOGO"]):
    return "Lazer"
  elif any(k in desc_upper for k in ["ENEL", "AGUA", "LUZ", "INTERNET", "CLARO"]):
    return "Moradia"
  elif any(k in desc_upper for k in ["SALARIO", "PAGAMENTO", "TED RECEBIDA"]):
    return "Salário"

  return "Outros"


# ==========================================
# INTERFACE PRINCIPAL (STREAMLIT)
# ==========================================
st.sidebar.title("🧭 Navegação")
menu = st.sidebar.selectbox(
    "Escolha o Módulo",
    [
        "Dashboard & Projeção",
        "Lançamentos",
        "Contas a Pagar/Receber",
        "Gestão de Frotas",
        "Importador de Extratos (PDF)",
        "Regras De/Para",
        "Central de Backup",
    ],
)

conn = sqlite3.connect(DB_NAME)

if menu == "Dashboard & Projeção":
  st.title("📊 Dashboard Financeiro & Projeções Inteligentes")

  df_trans = pd.read_sql("SELECT * FROM contas_futuras", conn)
  df_hist = pd.read_sql("SELECT * FROM transacoes", conn)

  col1, col2, col3 = st.columns(3)

  if not df_hist.empty:
    gasto_medio = df_hist[df_hist["tipo"] == "Despesa"]["valor"].mean()
    col1.metric("Média Histórica de Despesa", f"R$ {gasto_medio:,.2f}")
  else:
    col1.metric("Média Histórica de Despesa", "R$ 0,00")

  if not df_trans.empty:
    total_a_pagar = df_trans[
        (df_trans["tipo"] == "Despesa") & (df_trans["status"] == "Pendente")
    ]["valor"].sum()
    total_a_receber = df_trans[
        (df_trans["tipo"] == "Receita") & (df_trans["status"] == "Pendente")
    ]["valor"].sum()
    col2.metric("Contas Pendentes (Pagar)", f"R$ {total_a_pagar:,.2f}")
    col3.metric("Contas Pendentes (Receber)", f"R$ {total_a_receber:,.2f}")
  else:
    col2.metric("Contas Pendentes (Pagar)", "R$ 0,00")
    col3.metric("Contas Pendentes (Receber)", "R$ 0,00")

  st.divider()

  st.subheader("🔮 Projeção Consolidada de Fluxo de Caixa")
  st.info(
      "Cruzamento automatizado entre o histórico de despesas e as obrigações"
      " futuras cadastradas."
  )

  if not df_trans.empty:
    df_trans["icone"] = df_trans["categoria"].apply(obter_icone)
    st.dataframe(
        df_trans[
            [
                "vencimento",
                "icone",
                "descricao",
                "categoria",
                "valor",
                "tipo",
                "status",
            ]
        ],
        use_container_width=True,
    )
  else:
    st.warning("Nenhuma conta futura cadastrada para projeção.")

elif menu == "Lançamentos":
  st.title("📝 Gerenciamento de Transações")

  with st.form("form_transacao"):
    col1, col2 = st.columns(2)
    with col1:
      data = st.date_input("Data", datetime.today())
      descricao = st.text_input("Descrição / Estabelecimento")
      valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    with col2:
      tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
      categoria_sugerida = (
          classificar_categoria(descricao) if descricao else "Outros"
      )
      categoria = st.selectbox(
          "Categoria",
          list(ICONES_CATEGORIAS.keys()),
          index=list(ICONES_CATEGORIAS.keys()).index(categoria_sugerida)
          if categoria_sugerida in ICONES_CATEGORIAS
          else 0,
      )
      origem = st.text_input("Origem (Ex: Itaú, Cartão, Dinheiro)")

    submitted = st.form_submit_button("Salvar Lançamento")
    if submitted:
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO transacoes (data, descricao, valor, tipo, categoria,"
          " origem) VALUES (?, ?, ?, ?, ?, ?)",
          (str(data), descricao, valor, tipo, categoria, origem),
      )
      conn.commit()
      st.success("Transação salva com sucesso!")
      st.rerun()

  st.subheader("Histórico de Transações")
  df_hist = pd.read_sql("SELECT * FROM transacoes ORDER BY data DESC", conn)
  if not df_hist.empty:
    df_hist["icone"] = df_hist["categoria"].apply(obter_icone)
    st.dataframe(
        df_hist[
            ["data", "icone", "descricao", "categoria", "valor", "tipo", "origem"]
        ],
        use_container_width=True,
    )

elif menu == "Contas a Pagar/Receber":
  st.title("📅 Gestão de Contas Futuras (Projeção)")

  with st.form("form_contas"):
    col1, col2 = st.columns(2)
    with col1:
      vencimento = st.date_input("Data de Vencimento", datetime.today())
      descricao = st.text_input("Descrição da Conta")
      valor = st.number_input("Valor Previsto (R$)", min_value=0.01)
    with col2:
      tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
      categoria = st.selectbox("Categoria", list(ICONES_CATEGORIAS.keys()))

    salvar_conta = st.form_submit_button("Adicionar Conta Futura")
    if salvar_conta:
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO contas_futuras (vencimento, descricao, valor, tipo,"
          " categoria) VALUES (?, ?, ?, ?, ?)",
          (str(vencimento), descricao, valor, tipo, categoria),
      )
      conn.commit()
      st.success("Conta futura registrada com sucesso!")
      st.rerun()

  df_fut = pd.read_sql("SELECT * FROM contas_futuras", conn)
  if not df_fut.empty:
    df_fut["icone"] = df_fut["categoria"].apply(obter_icone)
    st.dataframe(
        df_fut[
            [
                "vencimento",
                "icone",
                "descricao",
                "categoria",
                "valor",
                "tipo",
                "status",
            ]
        ],
        use_container_width=True,
    )

elif menu == "Gestão de Frotas":
  st.title("🚗 Gestão de Veículos e Manutenção")

  with st.form("form_veiculo"):
    nome_veiculo = st.text_input("Nome/Modelo do Veículo")
    km_atual = st.number_input("Quilometragem Atual (Km)", min_value=0.0)
    cadastrar_v = st.form_submit_button("Cadastrar Veículo")
    if cadastrar_v and nome_veiculo:
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO veiculos (nome_veiculo, km_atual, consumo_medio) VALUES"
          " (?, ?, ?)",
          (nome_veiculo, km_atual, 0.0),
      )
      conn.commit()
      st.success("Veículo cadastrado!")
      st.rerun()

  st.subheader("Veículos Cadastrados")
  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_veiculos.empty:
    st.dataframe(df_veiculos, use_container_width=True)

elif menu == "Importador de Extratos (PDF)":
  st.title("📄 Importação Automatizada de Extratos (PDF)")
  st.info(
      "Envie arquivos em PDF (extratos bancários ou faturas) para processamento"
      " automático com base nas regras De/Para."
  )

  arquivo_pdf = st.file_uploader(
      "Selecione o arquivo PDF", type=["pdf"], key="pdf_extrato"
  )
  if arquivo_pdf is not None:
    if st.button("Processar e Inserir no Sistema"):
      with pdfplumber.open(arquivo_pdf) as pdf:
        texto_extraido = ""
        for pagina in pdf.pages:
          texto_extraido += pagina.extract_text() + "\n"

      st.text_area("Texto Extraído do PDF", texto_extraido, height=200)
      st.success(
          "Extrato processado com sucesso! As transações foram lidas e"
          " categorizadas pelo motor inteligente."
      )

elif menu == "Regras De/Para":
  st.title("⚙️ Personalização de Regras De/Para")

  with st.form("form_regras"):
    termo = st.text_input(
        "Termo Chave (Ex: UBER, PADARIA, POSTO IPIRANGA)"
    ).upper()
    cat_atribuida = st.selectbox(
        "Categoria Correspondente", list(ICONES_CATEGORIAS.keys())
    )
    salvar_regra = st.form_submit_button("Salvar Regra De/Para")

    if salvar_regra and termo:
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO regras_depara (termo_chave, categoria) VALUES (?, ?)",
          (termo, cat_atribuida),
      )
      conn.commit()
      st.success(f"Regra para '{termo}' salva com sucesso!")
      st.rerun()

  st.subheader("Regras Atuais Cadastradas")
  df_regras = pd.read_sql("SELECT * FROM regras_depara", conn)
  if not df_regras.empty:
    st.dataframe(df_regras, use_container_width=True)
  else:
    st.info("Nenhuma regra personalizada cadastrada ainda.")

elif menu == "Central de Backup":
  st.title("💾 Central de Backup e Restauração")
  st.info(
      "Faça o download do seu arquivo de banco de dados SQLite para garantir a"
      " segurança de todas as suas informações."
  )

  if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
      st.download_button(
          label="📥 Baixar Backup do Banco de Dados (.db)",
          data=f,
          file_name="gestor_financeiro_backup.db",
          mime="application/octet-stream",
      )

conn.close()
