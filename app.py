import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

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
c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
             (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS contas 
             (id INTEGER PRIMARY KEY, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)''')
conn.commit()

# --- TÍTULO ---
st.title("💸 Gestor Financeiro Profissional")

# Botão de Sair (Logout) na barra lateral
with st.sidebar:
    if st.button("🔒 Bloquear / Sair"):
        st.session_state.autenticado = False
        st.rerun()

# --- DEFINIÇÃO DAS ABAS ---
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "🔴 Lançar Despesa", 
    "🟢 Entradas & Salários", 
    "📊 Dashboard", 
    "❤️ Saúde Financeira", 
    "📅 Contas a Pagar", 
    "📋 Extrato & Backup"
])

# --- ABA 1: LANÇAR DESPESA ---
with aba1:
    st.subheader("Registrar Saída / Despesa")
    with st.form("lancar_despesa", clear_on_submit=True):
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
    with st.form("lancar_entrada", clear_on_submit=True):
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
    st.subheader("📊 Painel de Controle & Regra do 50/30/20")
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    df_contas = pd.read_sql("SELECT * FROM contas", conn)
    
    if not df.empty or not df_contas.empty:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        saldo_caixa = receitas - despesas
        
        total_contas_pendentes = 0
        if not df_contas.empty:
            total_contas_pendentes = df_contas[df_contas['pago'] == 0]['valor'].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Saldo em Caixa", f"R$ {saldo_caixa:.2f}")
        col2.metric("🟢 Total Entradas", f"R$ {receitas:.2f}")
        col3.metric("🔴 Total Despesas", f"R$ {despesas:.2f}")
        col4.metric("📅 Contas Pendentes", f"R$ {total_contas_pendentes:.2f}")

        st.markdown("---")
        dia_hoje = datetime.now().day
        projecao_final = (despesas / max(dia_hoje, 1)) * 30
        st.info(f"💡 **Projeção de Fechamento de Mês:** R$ {projecao_final:.2f}")

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
            st.warning("Cadastre ao menos uma entrada (Receita) para calcular as metas.")

        st.markdown("---")
        st.write("### Despesas por Categoria")
        df_desp = df[df['tipo'] == 'Despesa']
        if not df_desp.empty:
            st.bar_chart(df_desp.groupby('categoria')['valor'].sum())
    else:
        st.info("Comece registrando entradas e despesas para visualizar o dashboard.")

# --- ABA 4: SAÚDE FINANCEIRA (NOVA ABA ESTILO GESTORMONEY) ---
with aba4:
    st.subheader("❤️ Saúde Financeira")
    st.write("Score de 0 a 1000 baseado em fatores de desempenho do seu perfil financeiro.")
    
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    receitas = df[df['tipo'] == 'Receita']['valor'].sum() if not df.empty else 0
    despesas = df[df['tipo'] == 'Despesa']['valor'].sum() if not df.empty else 0
    
    # Lógica de cálculo do Score baseada nos seus dados reais
    # Fator 1: Endividamento (Gastos vs Receitas) -> Max 250 pts
    f_endividamento = 250 if receitas >= despesas else max(0, 250 - ((despesas - receitas) / max(receitas, 1)) * 250)
    
    # Fator 2: Taxa de Poupança/Investimento (Meta de 20%) -> Max 250 pts
    inv = df[df['categoria'].str.contains("Investimentos", na=False)]['valor'].sum() if not df.empty else 0
    taxa_poupanca = (inv / receitas) if receitas > 0 else 0
    f_poupanca = min(250, (taxa_poupanca / 0.20) * 250)
    
    # Fator 3: Controle de Desejos (Meta de gastar até 30% em desejos) -> Max 250 pts
    desejos = df[df['categoria'].str.contains("Desejos", na=False)]['valor'].sum() if not df.empty else 0
    proporcao_desejos = (desejos / receitas) if receitas > 0 else 0
    f_metas = 250 if proporcao_desejos <= 0.30 else max(0, 250 - ((proporcao_desejos - 0.30) * 500))
    
    # Fator 4: Disciplina Geral (Bônus fixo se houver lançamentos) -> Max 250 pts
    f_disciplina = 250 if not df.empty and receitas > 0 else 50
    
    score_total = int(f_endividamento + f_poupanca + f_metas + (f_disciplina * 0.5)) # Normalizado até 1000
    score_total = min(1000, max(0, score_total))
    
    # Classificação visual do Score
    if score_total >= 750:
        status_score, cor_status = "Excelente 🚀", "🟢"
    elif score_total >= 500:
        status_score, cor_status = "Bom 👍", "🔵"
    else:
        status_score, cor_status = "Atenção ⚠️", "🟠"

    # Exibição do Card Principal
    st.markdown(f"""
    <div style="background-color: #1E1E1E; padding: 30px; border-radius: 10px; text-align: center; border: 1px solid #333;">
        <h1 style="font-size: 60px; color: #FF4B4B; margin: 0;">{score_total}</h1>
        <p style="color: #888; font-size: 18px; margin: 5px 0 15px 0;">de 1000</p>
        <h3 style="color: #FFF; margin: 0;">{cor_status} {status_score}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Detalhamento por Fator")
    st.write("Avaliação baseada no seu volume atual de transações e metas.")
    
    st.write(f"🛡️ **Controle de Endividamento:** {int(f_endividamento)} / 250 pts")
    st.progress(min(f_endividamento / 250, 1.0))
    
    st.write(f"🎯 **Controle de Desejos (Regra 30%):** {int(f_metas)} / 250 pts")
    st.progress(min(f_metas / 250, 1.0))
    
    st.write(f"📈 **Taxa de Poupança / Investimento (Regra 20%):** {int(f_poupanca)} / 250 pts")
    st.progress(min(f_poupanca / 250, 1.0))
    
    st.write(f"📅 **Disciplina de Registros:** {int(f_disciplina * 0.5)} / 250 pts")
    st.progress(min((f_disciplina * 0.5) / 250, 1.0))

# --- ABA 5: CONTAS A PAGAR ---
with aba5:
    st.subheader("📅 Calendário de Contas & Gerenciamento")
    
    with st.form("conta", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            venc = st.date_input("Data de Vencimento")
            nome_conta = st.text_input("Nome da Conta (Ex: IPVA, Seguro, Aluguel)")
        with col_c2:
            val_conta = st.number_input("Valor Estimado", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("Adicionar ao Calendário", use_container_width=True):
            c.execute("INSERT INTO contas (vencimento, descricao, valor, pago) VALUES (?,?,?,?)", (venc, str(nome_conta), val_conta, 0))
            conn.commit()
            st.success("Conta adicionada com sucesso!")
            st.rerun()
            
    st.markdown("---")
    contas = pd.read_sql("SELECT * FROM contas", conn)
    
    if not contas.empty:
        st.write("### ❌ Excluir ou Marcar Conta")
        id_conta_del = st.selectbox("Selecione o ID da conta para gerenciar:", contas['id'].tolist(), key="del_conta")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Excluir Conta Selecionada", use_container_width=True):
                c.execute("DELETE FROM contas WHERE id = ?", (id_conta_del,))
                conn.commit()
                st.success(f"Conta ID {id_conta_del} excluída!")
                st.rerun()
        with col_btn2:
            if st.button("Alternar Status (Pago / Pendente)", use_container_width=True):
                status_atual = contas[contas['id'] == id_conta_del]['pago'].values[0]
                novo_status = 0 if status_atual == 1 else 1
                c.execute("UPDATE contas SET pago = ? WHERE id = ?", (novo_status, id_conta_del))
                conn.commit()
                st.success("Status atualizado!")
                st.rerun()

        st.markdown("---")
        st.write("### ✏️ Editar Conta")
        conta_atual = contas[contas['id'] == id_conta_del].iloc[0]
        
        with st.form("form_editar_conta"):
            nova_desc_conta = st.text_input("Descrição da Conta", value=conta_atual['descricao'])
            novo_val_conta = st.number_input("Valor Estimado (R$)", value=float(conta_atual['valor']), format="%.2f")
            
            if st.form_submit_button("Atualizar Conta", use_container_width=True):
                c.execute("UPDATE contas SET descricao = ?, valor = ? WHERE id = ?",
                          (nova_desc_conta, novo_val_conta, id_conta_del))
                conn.commit()
                st.success(f"Conta ID {id_conta_del} atualizada com sucesso!")
                st.rerun()

        st.markdown("---")
        st.subheader("Lista de Contas Cadastradas")
        st.dataframe(contas, use_container_width=Type := True)
    else:
        st.info("Nenhuma conta cadastrada no calendário.")

# --- ABA 6: EXTRATO & BACKUP ---
with aba6:
    st.subheader("📋 Extrato, Edição e Backup")
    
    # Botão de Backup do Banco de Dados
    with open("gestor_financeiro.db", "rb") as f:
        st.download_button("💾 Baixar Backup do Banco de Dados (Segurança)", f, "gestor_financeiro.db", use_container_width=True)

    st.markdown("---")
    df_extrato = pd.read_sql("SELECT * FROM transacoes", conn)
    
    if not df_extrato.empty:
        st.write("### ❌ Excluir Lançamento Específico")
        id_excluir = st.selectbox("Selecione o ID da transação para apagar:", df_extrato['id'].tolist())
        if st.button("Excluir Lançamento Selecionado"):
            c.execute("DELETE FROM transacoes WHERE id = ?", (id_excluir,))
            conn.commit()
            st.success(f"Transação ID {id_excluir} excluída com sucesso!")
            st.rerun()

        st.markdown("---")
        
        st.write("### ✏️ Editar Lançamento")
        id_editar = st.selectbox("Selecione o ID para editar:", df_extrato['id'].tolist(), key="select_edit")
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
