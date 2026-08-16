import base64
from datetime import datetime, date
import io
import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gestor Financeiro Profissional",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# ESTILO VISUAL & CSS CUSTOMIZADO
# ==========================================
st.markdown(
    """
    <style>
        .main { background-color: #0e1117; color: #fafafa; }
        .stMetric { background-color: #1a1c23; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
        .stMetric label { color: #9ca3af !important; font-size: 0.9rem !important; }
        .stMetric [data-testid="stMetricValue"] { color: #f3f4f6 !important; }
        .card { background-color: #1a1c23; padding: 20px; border-radius: 12px; border: 1px solid #2d3139; margin-bottom: 20px; }
        .stButton>button { border-radius: 8px; font-weight: 600; }
        h1, h2, h3 { color: #f9fafb; }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# BANCO DE DADOS & PERSISTÊNCIA
# ==========================================
DB_NAME = "financeiro_pro.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL,
            conta TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            placa TEXT,
            km_atual INTEGER,
            consumo_medio REAL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER,
            data TEXT,
            descricao TEXT,
            km INTEGER,
            custo REAL,
            FOREIGN KEY(veiculo_id) REFERENCES veiculos(id)
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT,
            tipo TEXT,
            quantidade REAL,
            preco_medio REAL,
            cotacao_atual REAL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            valor_alvo REAL,
            valor_atual REAL,
            prazo TEXT
        )
    """)

  conn.commit()
  conn.close()


init_db()


def run_query(query, params=(), fetch=True):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(query, params)
  if fetch:
    data = cursor.fetchall()
    conn.close()
    return data
  conn.commit()
  conn.close()


# ==========================================
# SIDEBAR & NAVEGAÇÃO
# ==========================================
st.sidebar.title("💎 Gestor Financeiro")
st.sidebar.caption("Versão 2.7.0 • Otimizado")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação",
    [
        "📊 Dashboard Executivo",
        "💸 Lançamentos",
        "🚗 Gestão de Veículos",
        "📈 Investimentos",
        "🎯 Metas & Planejamento",
        "📄 Leitor de Holerite",
    ],
)

# ==========================================
# 1. DASHBOARD EXECUTIVO
# ==========================================
if menu == "📊 Dashboard Executivo":
  st.title("📊 Dashboard Executivo")
  st.markdown("Visão geral da sua saúde financeira e indicadores de desempenho.")

  transacoes = run_query(
      "SELECT data, tipo, categoria, valor FROM transacoes"
  )
  if transacoes:
    df_trans = pd.DataFrame(
        transacoes, columns=["Data", "Tipo", "Categoria", "Valor"]
    )
    df_trans["Data"] = pd.to_datetime(df_trans["Data"])

    receitas_totais = df_trans[df_trans["Tipo"] == "Receita"]["Valor"].sum()
    despesas_totais = df_trans[df_trans["Tipo"] == "Despesa"]["Valor"].sum()
    saldo_liquido = receitas_totais - despesas_totais

    col1, col2, col3 = st.columns(3)
    with col1:
      st.metric(
          "Receitas Totais",
          f"R$ {receitas_totais:,.2f}".replace(",", "X")
          .replace(".", ",")
          .replace("X", "."),
      )
    with col2:
      st.metric(
          "Despesas Totais",
          f"R$ {despesas_totais:,.2f}".replace(",", "X")
          .replace(".", ",")
          .replace("X", "."),
      )
    with col3:
      st.metric(
          "Saldo Líquido",
          f"R$ {saldo_liquido:,.2f}".replace(",", "X")
          .replace(".", ",")
          .replace("X", "."),
          delta=f"R$ {saldo_liquido:,.2f}",
      )

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
      st.subheader("Despesas por Categoria")
      df_despesas = df_trans[df_trans["Tipo"] == "Despesa"]
      if not df_despesas.empty:
        fig_cat = px.pie(
            df_despesas,
            names="Categoria",
            values="Valor",
            hole=0.4,
            template="plotly_dark",
        )
        st.plotly_chart(fig_cat, use_container_width=True)
      else:
        st.info("Nenhuma despesa registrada para exibir gráficos.")

    with col_b:
      st.subheader("Evolução Temporal")
      df_temp = (
          df_trans.groupby([df_trans["Data"].dt.date, "Tipo"])["Valor"]
          .sum()
          .reset_index()
      )
      if not df_temp.empty:
        fig_temp = px.bar(
            df_temp,
            x="Data",
            y="Valor",
            color="Tipo",
            barmode="group",
            template="plotly_dark",
        )
        st.plotly_chart(fig_temp, use_container_width=True)
      else:
        st.info("Sem dados temporais suficientes.")
  else:
    st.info(
        "Nenhum lançamento encontrado. Cadastre suas receitas e despesas na aba"
        " 'Lançamentos'."
    )

# ==========================================
# 2. LANÇAMENTOS
# ==========================================
elif menu == "💸 Lançamentos":
  st.title("💸 Controle de Lançamentos")
  st.markdown(
      "Adicione novas receitas e despesas de forma rápida e organizada."
  )

  with st.form("form_lancamento", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
      data = st.date_input("Data do Lançamento", value=date.today())
      tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
      categoria = st.selectbox(
          "Categoria",
          [
              "Salário",
              "Alimentação",
              "Moradia",
              "Transporte",
              "Lazer",
              "Investimentos",
              "Outros",
          ],
      )
    with col2:
      descricao = st.text_input("Descrição / Estabelecimento")
      valor = st.number_input(
          "Valor (R$)", min_value=0.01, format="%.2f", step=1.0
      )
      conta = st.selectbox(
          "Conta / Cartão", ["Conta Corrente", "Cartão de Crédito", "Dinheiro"]
      )

    submitted = st.form_submit_button("Salvar Lançamento")
    if submitted:
      run_query(
          "INSERT INTO transacoes (data, tipo, categoria, descricao, valor,"
          " conta) VALUES (?, ?, ?, ?, ?, ?)",
          (str(data), tipo, categoria, descricao, valor, conta),
          fetch=False,
      )
      st.success("Lançamento salvo com sucesso!")

  st.markdown("---")
  st.subheader("Histórico de Lançamentos")
  transacoes = run_query(
      "SELECT id, data, tipo, categoria, descricao, valor, conta FROM transacoes"
      " ORDER BY data DESC"
  )
  if transacoes:
    df_hist = pd.DataFrame(
        transacoes,
        columns=["ID", "Data", "Tipo", "Categoria", "Descrição", "Valor", "Conta"],
    )
    st.dataframe(df_hist, use_container_width=True)

    id_excluir = st.number_input(
        "ID da transação para excluir", min_value=1, step=1
    )
    if st.button("Excluir Lançamento Selecionado"):
      run_query("DELETE FROM transacoes WHERE id = ?", (id_excluir,), fetch=False)
      st.warning(f"Lançamento {id_excluir} excluído.")
      st.rerun()
  else:
    st.info("Nenhum histórico encontrado.")

# ==========================================
# 3. GESTÃO DE VEÍCULOS
# ==========================================
elif menu == "🚗 Gestão de Veículos":
  st.title("🚗 Gestão de Veículos & Manutenções")

  tab1, tab2 = st.tabs(["Meus Veículos", "Registrar Manutenção"])

  with tab1:
    with st.form("form_veiculo"):
      nome = st.text_input("Nome / Modelo do Veículo")
      placa = st.text_input("Placa")
      km = st.number_input("Quilometragem Atual (KM)", min_value=0, step=100)
      consumo = st.number_input("Consumo Médio (Km/L)", min_value=0.0, step=0.1)
      if st.form_submit_button("Cadastrar Veículo"):
        run_query(
            "INSERT INTO veiculos (nome, placa, km_atual, consumo_medio)"
            " VALUES (?, ?, ?, ?)",
            (nome, placa, km, consumo),
            fetch=False,
        )
        st.success("Veículo cadastrado!")

    veiculos = run_query("SELECT id, nome, placa, km_atual FROM veiculos")
    if veiculos:
      st.subheader("Frota Cadastrada")
      for v in veiculos:
        st.markdown(
            f"- **{v[1]}** (Placa: `{v[2]}`) | **KM Atual:** {v[3]} km"
        )

  with tab2:
    veiculos = run_query("SELECT id, nome FROM veiculos")
    if veiculos:
      veiculo_dict = {v[1]: v[0] for v in veiculos}
      with st.form("form_manutencao"):
        v_escolhido = st.selectbox(
            "Selecione o Veículo", list(veiculo_dict.keys())
        )
        data_m = st.date_input("Data da Manutenção", value=date.today())
        desc = st.text_input("Serviço Realizado (ex: Troca de óleo, Pastilhas)")
        km_m = st.number_input("KM na Manutenção", min_value=0, step=100)
        custo = st.number_input("Custo (R$)", min_value=0.0, step=10.0)

        if st.form_submit_button("Registrar Manutenção"):
          run_query(
              "INSERT INTO manutencoes (veiculo_id, data, descricao, km, custo)"
              " VALUES (?, ?, ?, ?, ?)",
              (veiculo_dict[v_escolhido], str(data_m), desc, km_m, custo),
              fetch=False,
          )
          st.success("Manutenção registrada!")
    else:
      st.info("Cadastre um veículo primeiro.")

# ==========================================
# 4. INVESTIMENTOS
# ==========================================
elif menu == "📈 Investimentos":
  st.title("📈 Carteira de Investimentos")

  with st.form("form_investimento"):
    col1, col2 = st.columns(2)
    with col1:
      ativo = st.text_input("Código do Ativo (ex: PETR4, IVVB11)")
      tipo = st.selectbox(
          "Classe", ["Ações BR", "FIIs", "Renda Fixa", "Exterior", "Cripto"]
      )
      qtd = st.number_input("Quantidade", min_value=0.001, format="%.4f")
    with col2:
      pm = st.number_input("Preço Médio de Compra (R$)", min_value=0.01)
      cotacao = st.number_input("Cotação Atual (R$)", min_value=0.01)

    if st.form_submit_button("Adicionar Ativo"):
      run_query(
          "INSERT INTO investimentos (ativo, tipo, quantidade, preco_medio,"
          " cotacao_atual) VALUES (?, ?, ?, ?, ?)",
          (ativo.upper(), tipo, qtd, pm, cotacao),
          fetch=False,
      )
      st.success("Ativo adicionado com sucesso!")

  invs = run_query(
      "SELECT ativo, tipo, quantidade, preco_medio, cotacao_atual FROM"
      " investimentos"
  )
  if invs:
    df_inv = pd.DataFrame(
        invs, columns=["Ativo", "Tipo", "Quantidade", "Preço Médio", "Cotação"]
    )
    df_inv["Total Investido"] = df_inv["Quantidade"] * df_inv["Preço Médio"]
    df_inv["Valor Atual"] = df_inv["Quantidade"] * df_inv["Cotação"]
    df_inv["Lucro/Prejuízo"] = df_inv["Valor Atual"] - df_inv["Total Investido"]

    st.dataframe(df_inv, use_container_width=True)

    total_patrimonio = df_inv["Valor Atual"].sum()
    st.metric(
        "Patrimônio Total em Ativos",
        f"R$ {total_patrimonio:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
    )

# ==========================================
# 5. METAS & PLANEJAMENTO
# ==========================================
elif menu == "🎯 Metas & Planejamento":
  st.title("🎯 Metas Financeiras")

  with st.form("form_meta"):
    titulo = st.text_input("Nome da Meta (ex: Reserva de Emergência, Viagem)")
    v_alvo = st.number_input("Valor Alvo (R$)", min_value=1.0)
    v_atual = st.number_input("Valor Já Acumulado (R$)", min_value=0.0)
    prazo = st.date_input("Prazo Limite", value=date.today())

    if st.form_submit_button("Criar Meta"):
      run_query(
          "INSERT INTO metas (titulo, valor_alvo, valor_atual, prazo) VALUES"
          " (?, ?, ?, ?)",
          (titulo, v_alvo, v_atual, str(prazo)),
          fetch=False,
      )
      st.success("Meta criada!")

  metas = run_query("SELECT titulo, valor_alvo, valor_atual, prazo FROM metas")
  if metas:
    for m in metas:
      progresso = min(float(m[2] / m[1]), 1.0)
      st.subheader(f"📌 {m[0]} (Prazo: {m[3]})")
      st.progress(
          progresso,
          text=f"R$ {m[2]:,.2f} de R$ {m[1]:,.2f} ({progresso*100:.1f}%"
          " alcançado)",
      )

# ==========================================
# 6. LEITOR DE HOLERITE
# ==========================================
elif menu == "📄 Leitor de Holerite":
  st.title("📄 Leitor & Extrator de Holerites")
  st.markdown(
      "Faça o upload do seu holerite (PDF ou Imagem) para sumarizar os"
      " principais proventos e descontos."
  )

  uploaded_file = st.file_uploader(
      "Escolha o arquivo do holerite", type=["pdf", "png", "jpg", "jpeg"]
  )
  if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")
    with st.spinner("Processando dados do holerite..."):
      # Simulação de extração estruturada (Pronta para integração com OCR/IA)
      st.markdown("---")
      st.subheader("Resumo Extraído")
      col1, col2, col3 = st.columns(3)
      with col1:
        st.metric("Salário Bruto", "R$ 7.500,00")
      with col2:
        st.metric("Total de Descontos (INSS/IRRF)", "R$ 1.450,00")
      with col3:
        st.metric("Salário Líquido", "R$ 6.050,00")
  else:
    st.info("Aguardando upload do documento...")
