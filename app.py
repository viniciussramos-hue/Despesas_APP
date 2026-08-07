import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="💸 Gestor Financeiro Pro", layout="wide")

# --- SISTEMA DE SENHA / AUTENTICAÇÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acesso Restrito - Gestor Financeiro")
    senha_digitada = st.text_input("Digite a senha de acesso:", type="password")
    
    if st.button("Entrar", use_container_width=True):
        if senha_digitada == "1234":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta! Tente novamente.")
    st.stop()

# --- CONEXÃO BANCO DE DADOS ---
conn = sqlite3.connect("gestor_financeiro.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
             (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS contas 
             (id INTEGER PRIMARY KEY, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY, nome TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, categoria TEXT, valor_meta REAL)''')
conn.commit()

st.title("💸 Gestor Financeiro Profissional")

with st.sidebar:
    if st.button("🔒 Bloquear / Sair"):
        st.session_state.autenticado = False
        st.rerun()

aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs([
    "🔴 Lançar Despesa", "🟢 Entradas & Salários", "📊 Dashboard", 
    "🎯 Metas & Categorias", "❤️ Saúde Financeira", "📅 Contas a Pagar", "📋 Extrato & Backup"
])

# --- ABA 1 & 2: LANÇAMENTOS (ZERA AO CLICAR) ---
def renderizar_lancamento(tipo_trans):
    st.subheader(f"Registrar {tipo_trans}")
    cats_padrao = ["🏠 Contas Fixas", "🛒 Supermercado", "🚗 Transporte", "💊 Saúde", "🍔 Lazer", "📈 Investimentos"]
    db_cats = pd.read_sql("SELECT nome FROM categorias", conn)
    lista_cat = cats_padrao + db_cats['nome'].tolist()

    with st.form(f"form_{tipo_trans}", clear_on_submit=True):
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0, value=0.00, step=0.01, format="%.2f")
        cat = st.selectbox("Categoria", lista_cat)
        data = st.date_input("Data", value=date.today())
        
        if st.form_submit_button("Salvar", use_container_width=True):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data.strftime("%Y-%m-%d"), tipo_trans, desc, cat, valor))
            conn.commit()
            st.success(f"{tipo_trans} salva com sucesso!")

with aba1: renderizar_lancamento("Despesa")
with aba2: renderizar_lancamento("Receita")

# --- ABA 3: DASHBOARD ---
with aba3:
    st.subheader("📊 Painel de Controle")
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df.empty:
        df['valor'] = pd.to_numeric(df['valor'])
        df['data'] = pd.to_datetime(df['data'])
        df['mes'] = df['data'].dt.strftime('%Y-%m')
        mes = st.selectbox("Mês:", sorted(df['mes'].unique(), reverse=True))
        df_m = df[df['mes'] == mes]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo", f"R$ {df_m[df_m['tipo']=='Receita']['valor'].sum() - df_m[df_m['tipo']=='Despesa']['valor'].sum():,.2f}")
        c2.metric("Receitas", f"R$ {df_m[df_m['tipo']=='Receita']['valor'].sum():,.2f}")
        c3.metric("Despesas", f"R$ {df_m[df_m['tipo']=='Despesa']['valor'].sum():,.2f}")
        st.bar_chart(df_m.groupby('categoria')['valor'].sum())

# --- ABA 4: METAS & CATEGORIAS (COM ÍCONES) ---
with aba4:
    st.subheader("🎯 Metas e Categorias")
    c1, c2 = st.columns(2)
    with c1:
        with st.form("nova_cat", clear_on_submit=True):
            icone = st.selectbox("Ícone", ["✈️", "🐕", "🎮", "📚", "💻", "🍔", "🏠"])
            nome = st.text_input("Nome")
            if st.form_submit_button("Criar Categoria"):
                c.execute("INSERT INTO categorias (nome) VALUES (?)", (f"{icone} {nome}",))
                conn.commit()
                st.rerun()
    with c2:
        df_cats = pd.read_sql("SELECT * FROM categorias", conn)
        if not df_cats.empty:
            cat_del = st.selectbox("Excluir Categoria", df_cats['nome'].tolist())
            if st.button("Excluir Categoria"):
                c.execute("DELETE FROM categorias WHERE nome = ?", (cat_del,))
                conn.commit()
                st.rerun()

# --- DEMAIS ABAS (5, 6, 7) ---
# (Manter conforme seu padrão anterior, apenas garantindo os 'format="%.2f"' e 'value=0.00' nos inputs)
with aba7:
    st.info("Utilize a seção de importação para extratos CSV.")
    # (Inserir aqui a lógica de importação do código anterior)
