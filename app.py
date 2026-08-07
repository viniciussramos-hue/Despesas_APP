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

            st.success("Acesso liberado!")

            st.rerun()

        else:

            st.error("Senha incorreta! Tente novamente.")

    st.stop()



# --- CONEXÃO BANCO DE DADOS (PERSISTENTE) ---

conn = sqlite3.connect("gestor_financeiro.db", check_same_thread=False)

c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS contas (id INTEGER PRIMARY KEY, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY, nome TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, categoria TEXT, valor_meta REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS tabela_depositos (id INTEGER PRIMARY KEY, numero_deposito INTEGER, valor REAL, status TEXT)''')

conn.commit()



# Inicializa tabela de depósitos se vazia (Exemplo: 31 depósitos com valores de 1 a 31)

if pd.read_sql("SELECT count(*) FROM tabela_depositos", conn).iloc[0,0] == 0:

    for i in range(1, 32):

        c.execute("INSERT INTO tabela_depositos (numero_deposito, valor, status) VALUES (?, ?, ?)", (i, float(i), "Pendente"))

    conn.commit()



# --- TÍTULO ---

st.title("💸 Gestor Financeiro Profissional")



with st.sidebar:

    if st.button("🔒 Bloquear / Sair"):

        st.session_state.autenticado = False

        st.rerun()



# --- DEFINIÇÃO DAS ABAS ---

aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8 = st.tabs([

    "🔴 Lançar Despesa", "🟢 Entradas & Salários", "📊 Dashboard", "📈 Investimentos", 

    "🎯 Metas & Categorias", "❤️ Saúde Financeira", "📅 Contas a Pagar", "📋 Extrato & Backup"

])



# --- ABA 1: LANÇAR DESPESA ---

with aba1:

    st.subheader("Registrar Saída / Despesa")

    df_cats_db = pd.read_sql("SELECT nome FROM categorias", conn)

    lista_categorias = ["🏠 Contas Fixas (Necessidade)", "🛒 Supermercado (Necessidade)", "🚗 Transporte (Necessidade)", "💊 Saúde (Necessidade)", "🍔 Lazer & Alimentação Fora (Desejos)", "🎉 Outros Desejos (Desejos)", "📈 Investimentos / Poupança (20%)"] + df_cats_db['nome'].tolist()

    with st.form("lancar_despesa", clear_on_submit=True):

        desc = st.text_input("Descrição (Ex: Supermercado, Aluguel, Uber)")

        valor = st.number_input("Valor (R$)", min_value=0.0, value=0.00, format="%.2f")

        cat = st.selectbox("Categoria", lista_categorias)

        data_desp = st.date_input("Data do Gasto", value=date.today())

        if st.form_submit_button("Salvar Despesa", use_container_width=True):

            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)", (data_desp.strftime("%Y-%m-%d"), "Despesa", desc, cat, valor))

            conn.commit(); st.success("Despesa salva!")



# --- ABA 2: ENTRADAS ---

with aba2:

    st.subheader("Registrar Entrada (Salário, Vale, etc.)")

    with st.form("lancar_entrada", clear_on_submit=True):

        desc_rec = st.text_input("Descrição")

        valor_rec = st.number_input("Valor da Entrada (R$)", min_value=0.0, value=0.00, format="%.2f")

        cat_rec = st.selectbox("Tipo de Receita", ["Salário", "Vale", "13º Salário", "Férias", "Freelance / Extra", "Outras Receitas"])

        data_rec = st.date_input("Data de Recebimento", value=date.today())

        if st.form_submit_button("Salvar Entrada", use_container_width=True):

            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)", (data_rec.strftime("%Y-%m-%d"), "Receita", desc_rec, cat_rec, valor_rec))

            conn.commit(); st.success("Entrada registrada!")



# --- ABA 3: DASHBOARD ---

with aba3:

    st.subheader("📊 Painel de Controle")

    df_all = pd.read_sql("SELECT * FROM transacoes", conn)

    if not df_all.empty:

        df_all['data'] = pd.to_datetime(df_all['data'])

        df_all['ano_mes'] = df_all['data'].dt.strftime('%Y-%m')

        meses = sorted(df_all['ano_mes'].unique(), reverse=True)

        mes = st.selectbox("Filtrar por Mês:", meses)

        df = df_all[df_all['ano_mes'] == mes]

        st.line_chart(df.pivot_table(index='ano_mes', columns='tipo', values='valor', aggfunc='sum'))

        # Alerta 90%

        metas = pd.read_sql("SELECT * FROM metas", conn)

        for _, m in metas.iterrows():

            gasto = df[(df['categoria'] == m['categoria'])]['valor'].sum()

            if m['valor_meta'] > 0 and (gasto / m['valor_meta']) >= 0.9:

                st.warning(f"⚠️ Alerta: 90% da meta em {m['categoria']} atingida!")



# --- ABA 4: INVESTIMENTOS (TABELA DEPÓSITOS ESTILO COFRINHO) ---

with aba4:

    st.subheader("📈 Meta de Depósitos & Cofrinho")

    df_deps = pd.read_sql("SELECT * FROM tabela_depositos", conn)

    

    # Exibe o valor total acumulado no topo igualzinho à sua referência

    total_meta = df_deps['valor'].sum()

    st.markdown(f"<h3 style='color: #00FF7F; text-align: center;'>R$ {total_meta:,.2f}</h3>", unsafe_allow_html=True)



    df_exibicao = pd.DataFrame()

    df_exibicao['Nº do Depósito'] = df_deps['numero_deposito']

    df_exibicao['Valor a Guardar'] = df_deps['valor'].apply(lambda x: f"R$ {x:,.2f}")

    df_exibicao['Status'] = df_deps['status']



    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)



    st.markdown("---")

    st.subheader("⚙️ Atualizar Status do Depósito")

    c1, c2 = st.columns(2)

    sel = c1.selectbox("Selecione o Nº do Depósito:", df_deps['numero_deposito'].tolist())

    status = c2.selectbox("Alterar Status:", ["Pendente", "Concluído"])

    if st.button("Atualizar Status", use_container_width=True):

        c.execute("UPDATE tabela_depositos SET status = ? WHERE numero_deposito = ?", (status, sel))

        conn.commit()

        st.success(f"Depósito {sel} atualizado para '{status}'!")

        st.rerun()



# --- ABA 5: METAS & CATEGORIAS ---

with aba5:

    st.subheader("🎯 Metas & Categorias")

    with st.form("nova_cat", clear_on_submit=True):

        nome = st.text_input("Nova Categoria")

        if st.form_submit_button("Salvar"):

            c.execute("INSERT INTO categorias (nome) VALUES (?)", (nome,))

            conn.commit(); st.rerun()



# --- ABA 6: SAÚDE FINANCEIRA ---

with aba6:

    st.subheader("❤️ Saúde Financeira")

    df = pd.read_sql("SELECT * FROM transacoes", conn)

    st.metric("Score", int(1000 - (df[df['tipo']=='Despesa']['valor'].sum() - df[df['tipo']=='Receita']['valor'].sum()) * 0.1))



# --- ABA 7: CONTAS A PAGAR ---

with aba7:

    st.subheader("📅 Contas a Pagar")

    st.dataframe(pd.read_sql("SELECT * FROM contas", conn))



# --- ABA 8: EXTRATO & BACKUP ---

with aba8:

    st.subheader("📋 Extrato & Backup")

    if st.button("Baixar Banco (.db)"): st.download_button("Clique aqui", open("gestor_financeiro.db", "rb"), "gestor_financeiro.db")

    st.dataframe(pd.read_sql("SELECT * FROM transacoes", conn), use_container_width=True) 

