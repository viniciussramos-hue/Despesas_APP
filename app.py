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
c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
             (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, categoria TEXT, valor REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS contas 
             (id INTEGER PRIMARY KEY, vencimento TEXT, descricao TEXT, valor REAL, pago INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS categorias 
             (id INTEGER PRIMARY KEY, nome TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS metas 
             (id INTEGER PRIMARY KEY, categoria TEXT, valor_meta REAL)''')
conn.commit()

# --- TÍTULO ---
st.title("💸 Gestor Financeiro Profissional")

# Botão de Sair (Logout) na barra lateral
with st.sidebar:
    if st.button("🔒 Bloquear / Sair"):
        st.session_state.autenticado = False
        st.rerun()

# --- DEFINIÇÃO DAS ABAS ---
aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs([
    "🔴 Lançar Despesa", 
    "🟢 Entradas & Salários", 
    "📊 Dashboard", 
    "🎯 Metas & Categorias", 
    "❤️ Saúde Financeira", 
    "📅 Contas a Pagar", 
    "📋 Extrato & Backup"
])

# --- ABA 1: LANÇAR DESPESA ---
with aba1:
    st.subheader("Registrar Saída / Despesa")
    
    cats_padrao = [
        "🏠 Contas Fixas (Necessidade)", 
        "🛒 Supermercado (Necessidade)", 
        "🚗 Transporte (Necessidade)", 
        "💊 Saúde (Necessidade)", 
        "🍔 Lazer & Alimentação Fora (Desejos)", 
        "🎉 Outros Desejos (Desejos)", 
        "📈 Investimentos / Poupança (20%)"
    ]
    df_cats_db = pd.read_sql("SELECT nome FROM categorias", conn)
    lista_categorias = cats_padrao + df_cats_db['nome'].tolist() if not df_cats_db.empty else cats_padrao

    with st.form("lancar_despesa", clear_on_submit=True):
        desc = st.text_input("Descrição (Ex: Supermercado, Aluguel, Uber)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        cat = st.selectbox("Categoria", lista_categorias)
        data_desp = st.date_input("Data do Gasto", value=date.today())
        
        if st.form_submit_button("Salvar Despesa", use_container_width=True):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data_desp.strftime("%Y-%m-%d"), "Despesa", desc, cat, valor))
            conn.commit()
            st.success("Despesa salva com sucesso!")

# --- ABA 2: ENTRADAS & SALÁRIOS ---
with aba2:
    st.subheader("Registrar Entrada (Salário, Vale, Férias, 13º, etc.)")
    with st.form("lancar_entrada", clear_on_submit=True):
        desc_rec = st.text_input("Descrição (Ex: Salário Mensal, 13º Salário, Férias, Vale)")
        valor_rec = st.number_input("Valor da Entrada (R$)", min_value=0.0, format="%.2f")
        cat_rec = st.selectbox("Tipo de Receita", ["Salário", "Vale", "13º Salário", "Férias", "Freelance / Extra", "Outras Receitas"])
        data_rec = st.date_input("Data de Recebimento", value=date.today())
        if st.form_submit_button("Salvar Entrada", use_container_width=True):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data_rec.strftime("%Y-%m-%d"), "Receita", desc_rec, cat_rec, valor_rec))
            conn.commit()
            st.success("Entrada registrada com sucesso!")

# --- ABA 3: DASHBOARD COM FILTRO DE PERÍODO & GRÁFICOS PROFISSIONAIS ---
with aba3:
    st.subheader("📊 Painel de Controle Corporativo & Alertas")
    
    # --- FILTRO GLOBAL DE MÊS/ANO ---
    df_all = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df_all.empty:
        df_all['data'] = pd.to_datetime(df_all['data'])
        df_all['ano_mes'] = df_all['data'].dt.strftime('%Y-%m')
        meses_disponiveis = sorted(df_all['ano_mes'].unique(), reverse=True)
        
        col_f1, col_f2 = st.columns([2, 4])
        with col_f1:
            mes_selecionado = st.selectbox("Filtrar por Mês/Ano:", meses_disponiveis)
        
        # Filtra o dataframe pelo mês escolhido
        df = df_all[df_all['ano_mes'] == mes_selecionado].copy()
    else:
        df = df_all.copy()

    # --- NOTIFICAÇÕES DE CONTAS PENDENTES ---
    df_contas_check = pd.read_sql("SELECT * FROM contas WHERE pago = 0", conn)
    if not df_contas_check.empty:
        hoje = date.today()
        vencidas = []
        proximas = []
        
        for _, row in df_contas_check.iterrows():
            data_venc = datetime.strptime(row['vencimento'], "%Y-%m-%d").date()
            dias_diff = (data_venc - hoje).days
            
            if dias_diff < 0:
                vencidas.append(f"• **{row['descricao']}** (Vencia em {row['vencimento']} - R$ {row['valor']:.2f})")
            elif 0 <= dias_diff <= 3:
                proximas.append(f"• **{row['descricao']}** (Vence em {row['vencimento']} - R$ {row['valor']:.2f})")
                
        if vencidas:
            st.error("🚨 **Atenção! Contas VENCIDAS:**\n\n" + "\n".join(vencidas))
        if proximas:
            st.warning("⚠️ **Aviso: Contas próximas do vencimento (3 dias):**\n\n" + "\n".join(proximas))

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
        col1.metric("💰 Saldo do Período", f"R$ {saldo_caixa:.2f}")
        col2.metric("🟢 Entradas", f"R$ {receitas:.2f}")
        col3.metric("🔴 Despesas", f"R$ {despesas:.2f}")
        col4.metric("📅 Contas Pendentes", f"R$ {total_contas_pendentes:.2f}")

        st.markdown("---")
        
        # --- REGRA 50/30/20 ---
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
            st.warning("Cadastre ao menos uma entrada (Receita) neste período para calcular as metas.")

        st.markdown("---")
        
        # --- GRÁFICOS PROFISSIONAIS ---
        st.subheader("📈 Distribuição Analítica de Despesas")
        df_desp = df[df['tipo'] == 'Despesa']
        if not df_desp.empty:
            gasto_cat = df_desp.groupby('categoria')['valor'].sum()
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write("**Gráfico de Barras por Categoria**")
                st.bar_chart(gasto_cat)
            with col_g2:
                st.write("**Resumo Percentual de Gastos**")
                st.dataframe(gasto_cat.reset_index().rename(columns={'valor': 'Total Gasto (R$)'}), use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada para este mês.")
    else:
        st.info("Comece registrando entradas e despesas para visualizar o dashboard corporativo.")

# --- ABA 4: METAS & CATEGORIAS ---
with aba4:
    st.subheader("🎯 Gerenciamento de Metas de Gastos & Novas Categorias")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.write("### ➕ Adicionar Nova Categoria")
        with st.form("form_nova_cat", clear_on_submit=True):
            nova_cat_nome = st.text_input("Nome da Nova Categoria (Ex: ✈️ Viagens, 🐕 Pet)")
            if st.form_submit_button("Salvar Categoria", use_container_width=True):
                if nova_cat_nome.strip():
                    c.execute("INSERT INTO categorias (nome) VALUES (?)", (nova_cat_nome.strip(),))
                    conn.commit()
                    st.success(f"Categoria '{nova_cat_nome}' adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error("Digite um nome válido para a categoria.")
                    
    with col_m2:
        st.write("### 🎯 Definir Meta de Gasto por Categoria")
        cats_padrao = [
            "🏠 Contas Fixas (Necessidade)", 
            "🛒 Supermercado (Necessidade)", 
            "🚗 Transporte (Necessidade)", 
            "💊 Saúde (Necessidade)", 
            "🍔 Lazer & Alimentação Fora (Desejos)", 
            "🎉 Outros Desejos (Desejos)", 
            "📈 Investimentos / Poupança (20%)"
        ]
        df_cats_db = pd.read_sql("SELECT nome FROM categorias", conn)
        lista_todas_cats = cats_padrao + df_cats_db['nome'].tolist() if not df_cats_db.empty else cats_padrao

        with st.form("form_meta", clear_on_submit=True):
            cat_meta = st.selectbox("Escolha a Categoria", lista_todas_cats)
            valor_meta_input = st.number_input("Valor Máximo de Meta (R$)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Salvar Meta", use_container_width=True):
                c.execute("DELETE FROM metas WHERE categoria = ?", (cat_meta,))
                c.execute("INSERT INTO metas (categoria, valor_meta) VALUES (?, ?)", (cat_meta, valor_meta_input))
                conn.commit()
                st.success(f"Meta para '{cat_meta}' definida com sucesso!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Acompanhamento das Metas Cadastradas")
    df_metas = pd.read_sql("SELECT * FROM metas", conn)
    df_trans = pd.read_sql("SELECT * FROM transacoes WHERE tipo = 'Despesa'", conn)
    
    if not df_metas.empty:
        for index, row in df_metas.iterrows():
            cat_nome = row['categoria']
            v_meta = row['valor_meta']
            
            gasto_atual = df_trans[df_trans['categoria'] == cat_nome]['valor'].sum() if not df_trans.empty else 0.0
            
            st.write(f"**{cat_nome}** — Gasto: R$ {gasto_atual:.2f} / Meta: R$ {v_meta:.2f}")
            if v_meta > 0:
                st.progress(min(gasto_atual / v_meta, 1.0))
                if gasto_atual > v_meta:
                    st.error(f"⚠️ Você ultrapassou a meta de {cat_nome} em R$ {(gasto_atual - v_meta):.2f}!")
            else:
                st.progress(0.0)
    else:
        st.info("Nenhuma meta de gasto cadastrada ainda.")

# --- ABA 5: SAÚDE FINANCEIRA ---
with aba5:
    st.subheader("❤️ Saúde Financeira")
    st.write("Score de 0 a 1000 baseado em fatores de desempenho do seu perfil financeiro.")
    
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    receitas = df[df['tipo'] == 'Receita']['valor'].sum() if not df.empty else 0
    despesas = df[df['tipo'] == 'Despesa']['valor'].sum() if not df.empty else 0
    
    f_endividamento = 250 if receitas >= despesas else max(0, 250 - ((despesas - receitas) / max(receitas, 1)) * 250)
    
    inv = df[df['categoria'].str.contains("Investimentos", na=False)]['valor'].sum() if not df.empty else 0
    taxa_poupanca = (inv / receitas) if receitas > 0 else 0
    f_poupanca = min(250, (taxa_poupanca / 0.20) * 250)
    
    desejos = df[df['categoria'].str.contains("Desejos", na=False)]['valor'].sum() if not df.empty else 0
    proporcao_desejos = (desejos / receitas) if receitas > 0 else 0
    f_metas = 250 if proporcao_desejos <= 0.30 else max(0, 250 - ((proporcao_desejos - 0.30) * 500))
    
    f_disciplina = 250 if not df.empty and receitas > 0 else 50
    
    score_total = int(f_endividamento + f_poupanca + f_metas + (f_disciplina * 0.5))
    score_total = min(1000, max(0, score_total))
    
    if score_total >= 750:
        status_score, cor_status = "Excelente 🚀", "🟢"
    elif score_total >= 500:
        status_score, cor_status = "Bom 👍", "🔵"
    else:
        status_score, cor_status = "Atenção ⚠️", "🟠"

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

# --- ABA 6: CONTAS A PAGAR ---
with aba6:
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
        st.dataframe(contas, use_container_width=True)
    else:
        st.info("Nenhuma conta cadastrada no calendário.")

# --- ABA 7: EXTRATO, EXPORTAÇÃO EXCEL & BACKUP ---
with aba7:
    st.subheader("📋 Extrato Corporativo, Exportação e Backup")
    
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        # Botão de Backup do Banco de Dados
        with open("gestor_financeiro.db", "rb") as f:
            st.download_button("💾 Baixar Backup do Banco (.db)", f, "gestor_financeiro.db", use_container_width=True)
    with col_exp2:
        # Botão de Exportação para CSV / Excel
        df_extrato_full = pd.read_sql("SELECT * FROM transacoes", conn)
        if not df_extrato_full.empty:
            csv_data = df_extrato_full.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Exportar Extrato para Excel (CSV)",
                data=csv_data,
                file_name="extrato_financeiro.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("---")
    
    if not df_extrato_full.empty:
        st.write("### ❌ Excluir Lançamento Específico")
        id_excluir = st.selectbox("Selecione o ID da transação para apagar:", df_extrato_full['id'].tolist())
        if st.button("Excluir Lançamento Selecionado"):
            c.execute("DELETE FROM transacoes WHERE id = ?", (id_excluir,))
            conn.commit()
            st.success(f"Transação ID {id_excluir} excluída com sucesso!")
            st.rerun()

        st.markdown("---")
        
        st.write("### ✏️ Editar Lançamento")
        id_editar = st.selectbox("Selecione o ID para editar:", df_extrato_full['id'].tolist(), key="select_edit")
        item_atual = df_extrato_full[df_extrato_full['id'] == id_editar].iloc[0]
        
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
        st.dataframe(df_extrato_full, use_container_width=True)
        
        if st.button("🗑️ Limpar TODO o Extrato", use_container_width=True):
            c.execute("DELETE FROM transacoes")
            conn.commit()
            st.rerun()
    else:
        st.info("O extrato está vazio.")
