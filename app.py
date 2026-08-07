import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
conn = sqlite3.connect("gestor_financeiro.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
             (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS contas 
             (id INTEGER PRIMARY KEY, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)''')
conn.commit()

st.set_page_config(page_title="💸 Gestor Financeiro Pro", layout="wide")

# --- FUNÇÕES DE APOIO ---
def carregar_dados():
    return pd.read_sql("SELECT * FROM transacoes", conn)

st.title("💸 Gestor Financeiro Profissional")

# --- ABAS ---
aba1, aba2, aba3, aba4 = st.tabs(["➕ Lançar", "📊 Dashboard", "📅 Contas a Pagar", "📋 Extrato"])

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
    st.subheader("Dashboard e Metas")
    df = carregar_dados()
    if not df.empty:
        # Metas por Categoria (Exemplo de lógica)
        meta_alim = 800.0
        gasto_alim = df[(df['categoria'] == 'Alimentação') & (df['tipo'] == 'Despesa')]['valor'].sum()
        st.write(f"Meta Alimentação: R$ {gasto_alim:.2f} / R$ {meta_alim:.2f}")
        st.progress(min(gasto_alim/meta_alim, 1.0))
        
        # Filtro de Período
        st.markdown("---")
        data_ini = st.date_input("Início", datetime(2026, 1, 1))
        data_fim = st.date_input("Fim", datetime.now())
        
        df['data'] = pd.to_datetime(df['data'])
        df_f = df[(df['data'] >= pd.to_datetime(data_ini)) & (df['data'] <= pd.to_datetime(data_fim))]
        st.bar_chart(df_f.groupby('categoria')['valor'].sum())

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
