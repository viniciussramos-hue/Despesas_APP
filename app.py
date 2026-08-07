import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="💸 Gestor Financeiro Pro", layout="wide")

# --- SISTEMA DE SENHA ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    st.title("🔒 Acesso Restrito - Gestor Financeiro")
    if st.text_input("Digite a senha:", type="password") == "1234":
        st.session_state.autenticado = True
        st.rerun()
    st.stop()

# --- BANCO DE DADOS ---
conn = sqlite3.connect("gestor_financeiro.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS contas (id INTEGER PRIMARY KEY, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY, nome TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, categoria TEXT, valor_meta REAL)''')
conn.commit()

st.title("💸 Gestor Financeiro Profissional")

# --- ABAS ---
aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8 = st.tabs([
    "🔴 Lançar Despesa", "🟢 Entradas", "📊 Dashboard", "📈 Investimentos", 
    "🎯 Metas & Categorias", "❤️ Saúde Financeira", "📅 Contas a Pagar", "📋 Extrato & Backup"
])

# --- ABA 1 & 2: LANÇAMENTOS ---
def salvar_transacao(tipo):
    with st.form(f"f_{tipo}", clear_on_submit=True):
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0, value=0.00, format="%.2f")
        cats = ["Salário", "Contas Fixas", "Lazer", "Investimentos"] + pd.read_sql("SELECT nome FROM categorias", conn)['nome'].tolist()
        cat = st.selectbox("Categoria", cats)
        data = st.date_input("Data", value=date.today())
        if st.form_submit_button("Salvar"):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data.strftime("%Y-%m-%d"), tipo, desc, cat, valor))
            conn.commit(); st.success("Salvo!")

with aba1: salvar_transacao("Despesa")
with aba2: salvar_transacao("Receita")

# --- ABA 3: DASHBOARD ---
with aba3:
    st.subheader("📊 Painel de Controle")
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    df['data'] = pd.to_datetime(df['data'])
    df['mes'] = df['data'].dt.strftime('%Y-%m')
    mes = st.selectbox("Filtrar Mês:", sorted(df['mes'].unique(), reverse=True))
    
    metas = pd.read_sql("SELECT * FROM metas", conn)
    for _, m in metas.iterrows():
        gasto = df[(df['categoria'] == m['categoria']) & (df['mes'] == mes)]['valor'].sum()
        if m['valor_meta'] > 0 and (gasto / m['valor_meta']) >= 0.9:
            st.warning(f"⚠️ Alerta: 90% da meta de {m['categoria']} atingida!")
    
    if len(df['mes'].unique()) > 1:
        st.line_chart(df.pivot_table(index='mes', columns='tipo', values='valor', aggfunc='sum'))

# --- ABA 4: INVESTIMENTOS ---
with aba4:
    st.subheader("📈 Meus Investimentos")
    with st.form("inv", clear_on_submit=True):
        ativo = st.text_input("Ativo")
        valor = st.number_input("Valor (R$)", value=0.00, format="%.2f")
        if st.form_submit_button("Registrar"):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (date.today(), "Despesa", f"Inv: {ativo}", "📈 Investimentos", valor))
            conn.commit(); st.success("Registrado!")

# --- ABA 5: METAS & CATEGORIAS ---
with aba5:
    st.subheader("🎯 Metas e Categorias")
    if st.button("Limpar Metas"): c.execute("DELETE FROM metas"); conn.commit()
    st.dataframe(pd.read_sql("SELECT * FROM metas", conn))

# --- ABA 6: SAÚDE FINANCEIRA ---
with aba6:
    st.subheader("❤️ Score Financeiro")
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    rec = df[df['tipo']=='Receita']['valor'].sum()
    desp = df[df['tipo']=='Despesa']['valor'].sum()
    score = max(0, 1000 - (desp - rec) * 0.1) if desp > rec else 1000
    st.metric("Score de Saúde", int(score))

# --- ABA 7: CONTAS A PAGAR ---
with aba7:
    st.subheader("📅 Contas Pendentes")
    contas = pd.read_sql("SELECT * FROM contas", conn)
    st.dataframe(contas)

# --- ABA 8: EXTRATO & BACKUP ---
with aba8:
    st.write("### 📥 Importar CSV")
    file = st.file_uploader("Upload", type="csv")
    if file:
        pd.read_csv(file).to_sql("transacoes", conn, if_exists='append', index=False)
        st.success("Importado!")
    st.write("### 📋 Extrato Completo")
    st.dataframe(pd.read_sql("SELECT * FROM transacoes", conn))
