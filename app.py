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
aba1, aba2, aba3, aba4, aba5 = st.tabs(["🔴 Lançar Despesa", "🟢 Entradas & Salários", "📊 Dashboard", "📅 Contas a Pagar", "📋 Extrato"])

# --- ABA 1: LANÇAR DESPESA ---
with aba1:
    st.subheader("Registrar Saída / Despesa")
    with st.form("lancar_despesa"):
        desc = st.text_input("Descrição (Ex: Supermercado, Aluguel)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Contas Fixas", "Saúde", "Lazer", "Outros"])
        if st.form_submit_button("Salvar Despesa", use_container_width=True):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (datetime.now().strftime("%Y-%m-%d"), "Despesa", desc, cat, valor))
            conn.commit()
            st.success("Despesa salva com sucesso!")

# --- ABA 2: ENTRADAS & SALÁRIOS ---
with aba2:
    st.subheader("Registrar Entrada (Salário, Vale, Férias, 13º, etc.)")
    with st.form("lancar_entrada"):
        desc_rec = st.text_input("Descrição (Ex: Salário Mensal, 13º Salário, Férias, Vale)")
        valor_rec = st.number_input("Valor da Entrada (R$)", min_value=0.0, format="%.2f")
        cat_rec = st.selectbox("Tipo de Receita", ["Salário", "Vale", "13º Salário", "Férias", "Freelance / Extra", "Outras Receitas"])
        data_rec = st.date_input("Data de Recebimento")
        if st.form_submit_button("Salvar Entrada", use_container_width=True):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data_rec.strftime("%Y-%m-%d"), "Receita", desc_rec, cat_rec, valor_rec))
            conn.commit()
            st.success("Entrada registrada com sucesso!")

# --- ABA 3: DASHBOARD ---
with aba3:
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
        col1.metric("Total Entradas", f"R$ {receitas:.2f}")
        col2.metric("Total Despesas", f"R$ {despesas:.2f}")
        col3.metric("Saldo Atual em Caixa", f"R$ {receitas - despesas:.2f}", delta=f"R$ {receitas - despesas:.2f}")

        st.markdown("---")
        col_proj1, col_proj2 = st.columns(2)
        col_proj1.metric("Projeção de Gastos (Fim do Mês)", f"R$ {projecao_final:.2f}")

        st.markdown("---")
        st.write("### Despesas por Categoria")
        df_desp = df[df['tipo'] == 'Despesa']
        if not df_desp.empty:
            st.bar_chart(df_desp.groupby('categoria')['valor'].sum())
        else:
            st.info("Nenhuma despesa registrada para exibir o gráfico.")
    else:
        st.info("Comece registrando entradas e despesas para visualizar o dashboard.")

# --- ABA 4: CONTAS A PAGAR ---
with aba4:
    st.subheader("📅 Calendário de Contas Anuais / Mensais")
    with st.form("conta"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            venc = st.date_input("Data de Vencimento")
            nome_conta = st.text_input("Nome da Conta (Ex: IPVA, Seguro, Aluguel)")
        with col_c2:
            val_conta = st.number_input("Valor Estimado", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("Adicionar ao Calendário", use_container_width=True):
            c.execute("INSERT INTO contas (vencimento, descricao, valor, pago) VALUES (?,?,?,?)", (venc, nome_conta, val_conta, 0))
            conn.commit()
            st.rerun()
            
    st.markdown("---")
    contas = pd.read_sql("SELECT * FROM contas", conn)
    if not contas.empty:
        st.dataframe(contas, use_container_width=True)
    else:
        st.info("Nenhuma conta cadastrada no calendário.")

# --- ABA 5: EXTRATO ---
with aba5:
    st.subheader("📋 Extrato Completo de Transações")
    df_extrato = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df_extrato.empty:
        st.dataframe(df_extrato, use_container_width=True)
        if st.button("🗑️ Limpar Todas as Transações", use_container_width=True):
            c.execute("DELETE FROM transacoes")
            conn.commit()
            st.rerun()
    else:
        st.info("O extrato está vazio.")
