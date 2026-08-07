import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="💸 Gestor Financeiro Pro", layout="wide")

# Conexão Banco
conn = sqlite3.connect("gestor_financeiro.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
             (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS contas 
             (id INTEGER PRIMARY KEY, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)''')
conn.commit()

# --- TÍTULO ---
st.title("💸 Gestor Financeiro Profissional")

# --- DEFINIÇÃO DAS ABAS ---
aba1, aba2, aba3, aba4 = st.tabs(["➕ Lançar", "📊 Dashboard", "📅 Contas a Pagar", "📋 Extrato"])

# --- LÓGICA DAS ABAS ---
with aba1:
    col1, col2 = st.columns(2)
    with col1:
        with st.form("lancar"):
            tipo = st.radio("Tipo", ["Despesa", "Receita"])
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0)
            cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Contas Fixas", "Saúde", "Lazer", "Salário"])
            if st.form_submit_button("Salvar"):
                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                          (datetime.now().strftime("%Y-%m-%d"), tipo, desc, cat, valor))
                conn.commit()
                st.success("Salvo!")

with aba2:
    st.subheader("📊 Dashboard e Projeções")
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df.empty:
        df['valor'] = pd.to_numeric(df['valor'])
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        
        # Projeção
        dia_hoje = datetime.now().day
        projecao_final = (despesas / max(dia_hoje, 1)) * 30
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Saldo Atual", f"R$ {receitas - despesas:.2f}")
        col2.metric("Total Despesas", f"R$ {despesas:.2f}")
        col3.metric("Projeção Fim do Mês", f"R$ {projecao_final:.2f}")

        st.markdown("---")
        st.write("### Gastos por Categoria")
        df['data'] = pd.to_datetime(df['data'])
        st.bar_chart(df[df['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum())
    else:
        st.info("Lançe suas primeiras despesas para ver o dashboard.")

with aba3:
    st.subheader("📅 Calendário de Contas")
    with st.form("conta"):
        venc = st.date_input("Vencimento")
        nome_conta = st.text_input("Conta")
        val_conta = st.number_input("Valor da Conta")
        if st.form_submit_button("Adicionar Conta"):
            c.execute("INSERT INTO contas (vencimento, descricao, valor, pago) VALUES (?,?,?,?)", (venc, nome_conta, val_conta, 0))
            conn.commit()
            st.rerun()
            
    contas = pd.read_sql("SELECT * FROM contas", conn)
    st.table(contas)

with aba4:
    st.subheader("Extrato")
    st.dataframe(pd.read_sql("SELECT * FROM transacoes", conn), use_container_width=True)
    if st.button("Limpar Tudo"):
        c.execute("DELETE FROM transacoes")
        conn.commit()
        st.rerun()
