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
aba1, aba2, aba3, aba4, aba5 = st.tabs(["🔴 Lançar Despesa", "🟢 Entradas & Salários", "📊 Dashboard & 50/30/20", "📅 Contas a Pagar", "📋 Extrato & Edição"])

# --- ABA 1: LANÇAR DESPESA ---
with aba1:
    st.subheader("Registrar Saída / Despesa")
    with st.form("lancar_despesa"):
        desc = st.text_input("Descrição (Ex: Supermercado, Aluguel, Uber)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        cat = st.selectbox("Categoria", [
            "🏠 Contas Fixas (Necessidade)", 
            "🛒 Supermercado (Necessidade)", 
            "🚗 Transporte (Necessidade)", 
            "💊 Saúde (Necessidade)", 
            "🍔 Lazer & Alimentação Fora (Desejos)", 
            "🎉 Outros Desejos (Desejos)", 
            "📈 Investimentos / Poupança (20%)"
        ])
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

# --- ABA 3: DASHBOARD & 50/30/20 ---
with aba3:
    st.subheader("📊 Dashboard, Projeções & Regra do 50/30/20")
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df.empty:
        df['valor'] = pd.to_numeric(df['valor'])
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        
        # Projeção de Gastos
        dia_hoje = datetime.now().day
        projecao_final = (despesas / max(dia_hoje, 1)) * 30
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Entradas", f"R$ {receitas:.2f}")
        col2.metric("Total Despesas", f"R$ {despesas:.2f}")
        col3.metric("Saldo Atual em Caixa", f"R$ {receitas - despesas:.2f}")

        st.markdown("---")
        st.subheader("🎯 Acompanhamento da Regra 50 / 30 / 20")
        
        if receitas > 0:
            nec = df[df['categoria'].str.contains("Necessidade", na=False)]['valor'].sum()
            des = df[df['categoria'].str.contains("Desejos", na=False)]['valor'].sum()
            inv = df[df['categoria'].str.contains("Investimentos", na=False)]['valor'].sum()
            
            meta_nec = receitas * 0.50
            meta_des = receitas * 0.30
            meta_inv = receitas * 0.20
            
            c_50, c_30, c_20 = st.columns(3)
            
            with c_50:
                st.write("**50% Necessidades**")
                st.write(f"Gasto: R$ {nec:.2f} / Meta: R$ {meta_nec:.2f}")
                st.progress(min(nec / meta_nec if meta_nec > 0 else 0, 1.0))
                
            with c_30:
                st.write("**30% Desejos**")
                st.write(f"Gasto: R$ {des:.2f} / Meta: R$ {meta_des:.2f}")
                st.progress(min(des / meta_des if meta_des > 0 else 0, 1.0))
                
            with c_20:
                st.write("**20% Investimentos**")
                st.write(f"Guardado: R$ {inv:.2f} / Meta: R$ {meta_inv:.2f}")
                st.progress(min(inv / meta_inv if meta_inv > 0 else 0, 1.0))
        else:
            st.info("Cadastre ao menos uma entrada (Receita) para calcular as metas da regra 50/30/20.")

        st.markdown("---")
        st.write("### Despesas por Categoria")
        df_desp = df[df['tipo'] == 'Despesa']
        if not df_desp.empty:
            st.bar_chart(df_desp.groupby('categoria')['valor'].sum())
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

# --- ABA 5: EXTRATO & EDIÇÃO ---
with aba5:
    st.subheader("📋 Extrato e Gerenciamento de Lançamentos")
    df_extrato = pd.read_sql("SELECT * FROM transacoes", conn)
    
    if not df_extrato.empty:
        # Seção de Exclusão individual
        st.write("### ❌ Excluir Lançamento Específico")
        id_excluir = st.selectbox("Selecione o ID da transação para apagar:", df_extrato['id'].tolist())
        if st.button("Excluir Lançamento Selecionado"):
            c.execute("DELETE FROM transacoes WHERE id = ?", (id_excluir,))
            conn.commit()
            st.success(f"Transação ID {id_excluir} excluída com sucesso!")
            st.rerun()

        st.markdown("---")
        
        # Seção de Edição
        st.write("### ✏️ Editar Lançamento")
        id_editar = st.selectbox("Selecione o ID para editar:", df_extrato['id'].tolist(), key="select_edit")
        
        # Pega os dados atuais do ID selecionado
        item_atual = df_extrato[df_extrato['id'] == id_editar].iloc[0]
        
        with st.form("form_editar"):
            novo_tipo = st.selectbox("Tipo", ["Despesa", "Receita"], index=0 if item_atual['tipo'] == "Despesa" else 1)
            nova_desc = st.text_input("Descrição", value=item_atual['descricao'])
            novo_valor = st.number_input("Valor (R$)", value=float(item_atual['valor']), format="%.2f")
            nova_cat = st.text_input("Categoria", value=item_atual['categoria'])
            
            if st.form_submit_button("Atualizar Lançamento", use_container_width=True):
                c.execute("UPDATE transacoes SET tipo = ?, descricao = ?, categoria = ?, valor = ? WHERE id = ?",
                          (novo_tipo, nova_desc, nova_cat, novo_valor, id_editar))
                conn.commit()
                st.success(f"Transação ID {id_editar} atualizada com sucesso!")
                st.rerun()

        st.markdown("---")
        st.subheader("Visualização Completa do Extrato")
        st.dataframe(df_extrato, use_container_width=True)
        
        if st.button("🗑️ Limpar TODO o Extrato", use_container_width=True):
            c.execute("DELETE FROM transacoes")
            conn.commit()
            st.rerun()
    else:
        st.info("O extrato está vazio.")
