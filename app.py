import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import pdfplumber

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
c.execute('''CREATE TABLE IF NOT EXISTS carteira_investimentos 
             (id INTEGER PRIMARY KEY, data TEXT, ativo TEXT, classe TEXT, quantidade REAL, preco_medio REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS tabela_depositos 
             (id INTEGER PRIMARY KEY, numero_deposito INTEGER, valor REAL, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS cartao_credito 
             (id INTEGER PRIMARY KEY, data TEXT, cartao TEXT, descricao TEXT, categoria TEXT, valor REAL)''')
conn.commit()

# Inicializa a tabela de 200 depósitos apenas se estiver vazia
if pd.read_sql("SELECT count(*) FROM tabela_depositos", conn).iloc[0,0] == 0:
    for i in range(1, 201):
        c.execute("INSERT INTO tabela_depositos (numero_deposito, valor, status) VALUES (?, ?, ?)", (i, float(i), "Pendente"))
    conn.commit()

# --- FUNÇÃO DE CATEGORIZAÇÃO INTELIGENTE ---
def categorizar_automaticamente(descricao, tipo):
    desc_upper = descricao.upper()
    if tipo == "Receita":
        if "SALARIO" in desc_upper or "REMUNERACAO" in desc_upper:
            return "Salário"
        elif "TED" in desc_upper or "PIX" in desc_upper:
            return "Freelance / Extra"
        return "Outras Receitas"
    else:
        if any(x in desc_upper for x in ["SUPERMERCADO", "SHIBA", "MARKET", "ARMAZ", "BIG CENTER"]):
            return "🛒 Supermercado (Necessidade)"
        elif any(x in desc_upper for x in ["TELEFONICA", "EDP", "BOLETO", "ALUGUEL", "CONDOMINIO"]):
            return "🏠 Contas Fixas (Necessidade)"
        elif any(x in desc_upper for x in ["AUTO", "POSTO", "UBER", "BIKE", "IPVA"]):
            return "🚗 Transporte (Necessidade)"
        elif any(x in desc_upper for x in ["FARMACIA", "SAUDE", "MEDICO"]):
            return "💊 Saúde (Necessidade)"
        elif any(x in desc_upper for x in ["RESTAURANTE", "LANCHE", "PASTE", "PANIF", "BAR"]):
            return "🍔 Lazer & Alimentação Fora (Desejos)"
        elif any(x in desc_upper for x in ["GOOGLE", "SPOTIFY", "STEAM", "JOGO", "NETFLIX"]):
            return "🎉 Outros Desejos (Desejos)"
        elif "INVEST" in desc_upper or "ACOES" in desc_upper:
            return "📈 Investimentos / Poupança (20%)"
        return "🏠 Contas Fixas (Necessidade)"

# --- TÍTULO ---
st.title("💸 Gestor Financeiro Profissional")

# Barra Lateral (Logout & Assinatura)
with st.sidebar:
    if st.button("🔒 Bloquear / Sair"):
        st.session_state.autenticado = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #888; font-size: 12px;'>Elaborado por Vinicius Ramos</p>", unsafe_allow_html=True)

# --- DEFINIÇÃO DAS ABAS (11 Abas) ---
aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10, aba11 = st.tabs([
    "🔴 Lançar Despesa", 
    "🟢 Entradas & Salários", 
    "📊 Dashboard", 
    "💳 Cartão de Crédito",
    "📈 Investimentos", 
    "🎯 Desafios", 
    "🎯 Metas & Categorias", 
    "❤️ Saúde Financeira", 
    "🔮 Projeção & Caixa",
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
        valor = st.number_input("Valor (R$)", min_value=0.0, value=0.00, step=1.0, format="%.2f")
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
        valor_rec = st.number_input("Valor da Entrada (R$)", min_value=0.0, value=0.00, step=1.0, format="%.2f")
        cat_rec = st.selectbox("Tipo de Receita", ["Salário", "Vale", "13º Salário", "Férias", "Freelance / Extra", "Outras Receitas"])
        data_rec = st.date_input("Data de Recebimento", value=date.today())
        if st.form_submit_button("Salvar Entrada", use_container_width=True):
            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data_rec.strftime("%Y-%m-%d"), "Receita", desc_rec, cat_rec, valor_rec))
            conn.commit()
            st.success("Entrada registrada com sucesso!")

# --- ABA 3: DASHBOARD ---
with aba3:
    st.subheader("📊 Painel de Controle Corporativo & Alertas")
    
    df_all = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df_all.empty:
        df_all['data'] = pd.to_datetime(df_all['data'])
        df_all['ano_mes'] = df_all['data'].dt.strftime('%Y-%m')
        meses_disponiveis = sorted(df_all['ano_mes'].unique(), reverse=True)
        
        col_f1, col_f2 = st.columns([2, 4])
        with col_f1:
            mes_selecionado = st.selectbox("Filtrar por Mês/Ano:", meses_disponiveis)
        
        df = df_all[df_all['ano_mes'] == mes_selecionado].copy()
    else:
        df = df_all.copy()

    # Alerta de Gastos Anômalos (Comparação com a média histórica)
    if not df_all.empty and not df.empty:
        df_desp_all = df_all[df_all['tipo'] == 'Despesa']
        if len(df_desp_all['ano_mes'].unique()) > 1:
            media_por_cat = df_desp_all.groupby(['categoria', 'ano_mes'])['valor'].sum().reset_index()
            media_historica = media_por_cat.groupby('categoria')['valor'].mean().to_dict()
            
            gasto_atual_cat = df[df['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().to_dict()
            for cat, val in gasto_atual_cat.items():
                med = media_historica.get(cat, val)
                if med > 0 and val > (med * 1.3):  # 30% acima da média histórica
                    st.warning(f"🚨 **Alerta de Gasto Anômalo:** Os gastos em **{cat}** (R$ {val:,.2f}) estão 30% acima da sua média histórica (R$ {med:,.2f})!")

    metas_check = pd.read_sql("SELECT * FROM metas", conn)
    if not df.empty and not metas_check.empty:
        for _, m in metas_check.iterrows():
            gasto_cat_mes = df[(df['categoria'] == m['categoria']) & (df['tipo'] == 'Despesa')]['valor'].sum()
            if m['valor_meta'] > 0 and (gasto_cat_mes / m['valor_meta']) >= 0.9:
                st.warning(f"⚠️ **Alerta de Orçamento:** Você atingiu ou ultrapassou 90% da meta em **{m['categoria']}**! (Gasto: R$ {gasto_cat_mes:,.2f} / Meta: R$ {m['valor_meta']:,.2f})")

    df_contas_check = pd.read_sql("SELECT * FROM contas WHERE pago = 0", conn)
    if not df_contas_check.empty:
        hoje = date.today()
        vencidas = []
        proximas = []
        
        for _, row in df_contas_check.iterrows():
            data_venc = datetime.strptime(row['vencimento'], "%Y-%m-%d").date()
            dias_diff = (data_venc - hoje).days
            
            if dias_diff < 0:
                vencidas.append(f"• **{row['descricao']}** (Vencia em {row['vencimento']} - R$ {row['valor']:,.2f})")
            elif 0 <= dias_diff <= 3:
                proximas.append(f"• **{row['descricao']}** (Vence em {row['vencimento']} - R$ {row['valor']:,.2f})")
                
        if vencidas:
            st.error("🚨 **Atenção! Contas VENCIDAS:**\n\n" + "\n".join(vencidas))
        if proximas:
            st.warning("⚠️ **Aviso: Contas próximas do vencimento (3 dias):**\n\n" + "\n".join(proximas))

    df_contas = pd.read_sql("SELECT * FROM contas", conn)
    
    if not df_all.empty:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        saldo_caixa = receitas - despesas
        
        total_contas_pendentes = 0
        if not df_contas.empty:
            total_contas_pendentes = df_contas[df_contas['pago'] == 0]['valor'].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Saldo do Período", f"R$ {saldo_caixa:,.2f}")
        col2.metric("🟢 Entradas", f"R$ {receitas:,.2f}")
        col3.metric("🔴 Despesas", f"R$ {despesas:,.2f}")
        col4.metric("📅 Contas Pendentes", f"R$ {total_contas_pendentes:,.2f}")

        st.markdown("---")
        
        st.subheader("🎯 Acompanhamento da Regra 50 / 30 / 20")
        if receitas > 0:
            nec = df[(df['tipo'] == 'Despesa') & (df['categoria'].str.contains("Necessidade", na=False))]['valor'].sum()
            des = df[(df['tipo'] == 'Despesa') & (df['categoria'].str.contains("Desejos", na=False))]['valor'].sum()
            inv = df[(df['tipo'] == 'Despesa') & (df['categoria'].str.contains("Investimentos", na=False))]['valor'].sum()
            
            meta_nec = receitas * 0.50
            meta_des = receitas * 0.30
            meta_inv = receitas * 0.20
            
            c_50, c_30, c_20 = st.columns(3)
            with c_50:
                st.write("**50% Necessidades**")
                st.write(f"Gasto: R$ {nec:,.2f} / Meta: R$ {meta_nec:,.2f}")
                st.progress(min(nec / meta_nec if meta_nec > 0 else 0, 1.0))
            with c_30:
                st.write("**30% Desejos**")
                st.write(f"Gasto: R$ {des:,.2f} / Meta: R$ {meta_des:,.2f}")
                st.progress(min(des / meta_des if meta_des > 0 else 0, 1.0))
            with c_20:
                st.write("**20% Investimentos**")
                st.write(f"Guardado: R$ {inv:,.2f} / Meta: R$ {meta_inv:,.2f}")
                st.progress(min(inv / meta_inv if meta_inv > 0 else 0, 1.0))
        else:
            st.warning("Cadastre ao menos uma entrada (Receita) neste período para calcular as metas.")

        st.markdown("---")
        st.subheader("📈 Distribuição Analítica de Despesas (Mês Selecionado)")
        df_desp = df[df['tipo'] == 'Despesa']
        if not df_desp.empty:
            gasto_cat = df_desp.groupby('categoria')['valor'].sum()
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write("**Gráfico de Barras por Categoria**")
                st.bar_chart(gasto_cat)
            with col_g2:
                st.write("**Resumo Percentual de Gastos**")
                df_resumo = gasto_cat.reset_index().rename(columns={'valor': 'Total Gasto (R$)'})
                df_resumo['Total Gasto (R$)'] = df_resumo['Total Gasto (R$)'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_resumo, use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada para este mês.")
            
        st.markdown("---")
        st.subheader("📈 Evolução e Saldo Acumulado Histórico")
        df_pivot = df_all.pivot_table(index='ano_mes', columns='tipo', values='valor', aggfunc='sum').fillna(0)
        if 'Receita' not in df_pivot.columns: df_pivot['Receita'] = 0
        if 'Despesa' not in df_pivot.columns: df_pivot['Despesa'] = 0
        
        df_pivot['Saldo Mensal'] = df_pivot['Receita'] - df_pivot['Despesa']
        df_pivot['Saldo Acumulado'] = df_pivot['Saldo Mensal'].cumsum()
        
        st.write("**Gráfico de Saldo Acumulado (Evolução do Patrimônio em Caixa)**")
        st.line_chart(df_pivot[['Saldo Acumulado']])
        
        st.write("**Comparativo Mensal (Receitas vs Despesas)**")
        st.line_chart(df_pivot[['Receita', 'Despesa']])
        
    else:
        st.info("Comece registrando entradas e despesas para visualizar o dashboard corporativo.")

# --- ABA 4: CARTÃO DE CRÉDITO ---
with aba4:
    st.subheader("💳 Gestão Detalhada de Cartão de Crédito")
    st.info("Cadastre os gastos individuais do cartão para acompanhar quais compras pesam mais na fatura.")
    
    with st.form("form_cartao", clear_on_submit=True):
        col_cc1, col_cc2 = st.columns(2)
        with col_cc1:
            nome_cartao = st.selectbox("Cartão", ["Itaúcard", "Samsung Itaú", "Nubank", "Outro"])
            desc_cc = st.text_input("Descrição da Compra (Ex: Lojas Americanas, Uber)")
        with col_cc2:
            val_cc = st.number_input("Valor da Compra (R$)", min_value=0.0, value=0.00, step=1.0, format="%.2f")
            data_cc = st.date_input("Data da Compra", value=date.today())
            
        cat_cc = st.selectbox("Categoria da Compra", [
            "🛒 Supermercado (Necessidade)", 
            "🏠 Contas Fixas (Necessidade)", 
            "🚗 Transporte (Necessidade)", 
            "💊 Saúde (Necessidade)", 
            "🍔 Lazer & Alimentação Fora (Desejos)", 
            "🎉 Outros Desejos (Desejos)"
        ])
        
        if st.form_submit_button("Adicionar Gasto ao Cartão", use_container_width=True):
            c.execute("INSERT INTO cartao_credito (data, cartao, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data_cc.strftime("%Y-%m-%d"), nome_cartao, desc_cc, cat_cc, val_cc))
            conn.commit()
            st.success("Compra no cartão registrada com sucesso!")
            st.rerun()

    st.markdown("---")
    df_cartao = pd.read_sql("SELECT * FROM cartao_credito", conn)
    if not df_cartao.empty:
        st.write("### 📋 Fatura Detalhada de Cartões")
        st.dataframe(df_cartao, use_container_width=True)
        
        total_fatura = df_cartao['valor'].sum()
        st.metric("💳 Total Acumulado em Faturas", f"R$ {total_fatura:,.2f}")
        
        id_del_cc = st.selectbox("Selecione o ID da compra no cartão para remover:", df_cartao['id'].tolist())
        if st.button("Remover Compra Selecionada", use_container_width=True):
            c.execute("DELETE FROM cartao_credito WHERE id = ?", (id_del_cc,))
            conn.commit()
            st.success("Compra removida do cartão!")
            st.rerun()
    else:
        st.info("Nenhuma compra registrada nos cartões ainda.")

# --- ABA 5: DASHBOARD PROFISSIONAL DE INVESTIMENTOS ---
with aba5:
    st.subheader("📈 Dashboard Profissional de Investimentos & Carteira")
    
    with st.form("form_ativo_inv", clear_on_submit=True):
        col_iv1, col_iv2, col_iv3 = st.columns(3)
        with col_iv1:
            ativo_nome = st.text_input("Ativo / Ticker (Ex: PETR4, Tesouro Direto, FII)")
            classe_ativo = st.selectbox("Classe de Ativo", ["Ações BR", "FIIs", "Renda Fixa", "Criptomoedas", "Exterior"])
        with col_iv2:
            qtd_ativo = st.number_input("Quantidade / Cotas", min_value=0.0001, value=1.00, step=1.0)
            preco_medio = st.number_input("Preço Médio / Custo Unitário (R$)", min_value=0.0, value=0.00, step=0.10, format="%.2f")
        with col_iv3:
            data_aporte = st.date_input("Data do Aporte", value=date.today())
            st.write("")
            st.write("")
            btn_add_ativo = st.form_submit_button("Cadastrar Posição na Carteira", use_container_width=True)
            
        if btn_add_ativo:
            if ativo_nome.strip():
                c.execute("INSERT INTO carteira_investimentos (data, ativo, classe, quantidade, preco_medio) VALUES (?,?,?,?,?)",
                          (data_aporte.strftime("%Y-%m-%d"), ativo_nome.upper().strip(), classe_ativo, qtd_ativo, preco_medio))
                conn.commit()
                st.success(f"Ativo {ativo_nome.upper()} cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome do ativo.")

    st.markdown("---")
    
    df_carteira = pd.read_sql("SELECT * FROM carteira_investimentos", conn)
    if not df_carteira.empty:
        df_carteira['Valor Total'] = df_carteira['quantidade'] * df_carteira['preco_medio']
        patrimonio_total = df_carteira['Valor Total'].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("💎 Patrimônio Alocado", f"R$ {patrimonio_total:,.2f}")
        col_m2.metric("📦 Total de Ativos Cadastrados", len(df_carteira['ativo'].unique()))
        col_m3.metric("📊 Classes de Ativos", len(df_carteira['classe'].unique()))
        
        st.markdown("---")
        
        col_pos1, col_pos2 = st.columns(2)
        with col_pos1:
            st.write("### 📊 Alocação por Classe de Ativos")
            df_classe = df_carteira.groupby('classe')['Valor Total'].sum()
            st.bar_chart(df_classe)
        with col_pos2:
            st.write("### 📋 Posições Detalhadas na Carteira")
            st.dataframe(df_carteira[['ativo', 'classe', 'quantidade', 'preco_medio', 'Valor Total']].rename(columns={
                'ativo': 'Ativo', 'classe': 'Classe', 'quantidade': 'Qtd', 'preco_medio': 'Preço Médio'
            }), use_container_width=True, hide_index=True)
            
        st.markdown("---")
        id_ativo_del = st.selectbox("Selecione o ID do ativo para remover da carteira:", df_carteira['id'].tolist(), key="del_ativo")
        if st.button("Remover Ativo Selecionado", use_container_width=True):
            c.execute("DELETE FROM carteira_investimentos WHERE id = ?", (id_ativo_del,))
            conn.commit()
            st.success("Ativo removido!")
            st.rerun()
    else:
        st.info("Nenhum investimento cadastrado na carteira profissional ainda. Adicione acima para ver o dashboard avançado.")

# --- ABA 6: DESAFIOS ---
with aba6:
    st.subheader("🎯 Desafio de Depósito (R$ 20.100,00 em 200 Depósitos)")
    st.info("Acompanhe o seu progresso rumo à meta total de R$ 20.100,00 dividida em 200 depósitos progressivos!")
    
    df_deps = pd.read_sql("SELECT * FROM tabela_depositos", conn)
    total_concluido = df_deps[df_deps['status'] == 'Concluído']['valor'].sum()
    meta_total_desafio = df_deps['valor'].sum() 
    
    st.markdown(f"<h3 style='color: #00FF7F; text-align: center;'>Progresso do Desafio: R$ {total_concluido:,.2f} / R$ {meta_total_desafio:,.2f}</h3>", unsafe_allow_html=True)
    st.progress(min(total_concluido / meta_total_desafio if meta_total_desafio > 0 else 0, 1.0))

    col_esq, col_dir = st.columns([2, 1])

    with col_esq:
        st.write("### Tabela do Desafio")
        df_exibicao = pd.DataFrame()
        df_exibicao['Nº do Depósito'] = df_deps['numero_deposito']
        df_exibicao['Valor a Guardar'] = df_deps['valor'].apply(lambda x: f"R$ {x:,.2f}")
        df_exibicao['Status'] = df_deps['status']
        
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True, height=350)

    with col_dir:
        st.write("### ⚙️ Atualizar Status")
        with st.form("form_atualizar_deposito"):
            dep_sel = st.selectbox("Selecione o Nº do Depósito:", df_deps['numero_deposito'].tolist())
            
            status_atual_obj = df_deps[df_deps['numero_deposito'] == dep_sel]['status'].values
            index_atual = 0 if len(status_atual_obj) > 0 and status_atual_obj[0] == "Pendente" else 1
            
            status_novo = st.selectbox("Novo Status:", ["Pendente", "Concluído"], index=index_atual)
            
            if st.form_submit_button("Salvar Alteração", use_container_width=True):
                c.execute("UPDATE tabela_depositos SET status = ? WHERE numero_deposito = ?", (status_novo, dep_sel))
                conn.commit()
                st.success(f"Depósito {dep_sel} atualizado para '{status_novo}'!")
                st.rerun()

        if st.button("🔄 Marcar todos como Pendentes", use_container_width=True):
            c.execute("UPDATE tabela_depositos SET status = 'Pendente'")
            conn.commit()
            st.rerun()

# --- ABA 7: METAS & CATEGORIAS ---
with aba7:
    st.subheader("🎯 Gerenciamento de Metas, Ícones e Categorias")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.write("### ➕ Adicionar Nova Categoria com Ícone")
        with st.form("form_nova_cat", clear_on_submit=True):
            icone_escolhido = st.selectbox("Escolha um Ícone:", ["✈️", "🐕", "🎮", "📚", "💻", "💄", "⚡", "🏋️‍♂️", "🍔", "🎁", "🚗", "🏠"])
            nome_cat_input = st.text_input("Nome da Categoria (Ex: Viagens, Pet, Jogos)")
            
            if st.form_submit_button("Salvar Categoria", use_container_width=True):
                if nome_cat_input.strip():
                    categoria_final = f"{icone_escolhido} {nome_cat_input.strip()}"
                    c.execute("INSERT INTO categorias (nome) VALUES (?)", (categoria_final,))
                    conn.commit()
                    st.success(f"Categoria '{categoria_final}' adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error("Digite um nome válido para a categoria.")
        
        st.markdown("---")
        st.write("### 🗑️ Excluir Categoria Personalizada")
        df_cats_excluir = pd.read_sql("SELECT * FROM categorias", conn)
        if not df_cats_excluir.empty:
            cat_para_deletar = st.selectbox("Selecione a categoria para apagar:", df_cats_excluir['nome'].tolist(), key="del_cat_select")
            if st.button("Excluir Categoria Selecionada", use_container_width=True):
                c.execute("DELETE FROM categorias WHERE nome = ?", (cat_para_deletar,))
                conn.commit()
                st.success(f"Categoria '{cat_para_deletar}' excluída com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma categoria personalizada para excluir.")
                    
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
            valor_meta_input = st.number_input("Valor Máximo de Meta (R$)", min_value=0.0, value=0.00, step=1.0, format="%.2f")
            
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
            
            st.write(f"**{cat_nome}** — Gasto: R$ {gasto_atual:,.2f} / Meta: R$ {v_meta:,.2f}")
            if v_meta > 0:
                st.progress(min(gasto_atual / v_meta, 1.0))
                if gasto_atual > v_meta:
                    st.error(f"⚠️ Você ultrapassou a meta de {cat_nome} em R$ {(gasto_atual - v_meta):,.2f}!")
            else:
                st.progress(0.0)
    else:
        st.info("Nenhuma meta de gasto cadastrada ainda.")

# --- ABA 8: SAÚDE FINANCEIRA ---
with aba8:
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

# --- ABA 9: PROJEÇÃO & FLUXO DE CAIXA DIÁRIO ---
with aba9:
    st.subheader("🔮 Projeção Financeira & Fluxo de Caixa Diário")
    st.info("Acompanhe a projeção dos próximos meses e o fluxo de caixa diário dos seus lançamentos.")
    
    df_all_proj = pd.read_sql("SELECT * FROM transacoes", conn)
    
    if not df_all_proj.empty:
        df_all_proj['data'] = pd.to_datetime(df_all_proj['data'])
        df_all_proj['ano_mes'] = df_all_proj['data'].dt.strftime('%Y-%m')
        
        st.write("### 📅 Fluxo de Caixa Diário (Saldo Acumulado por Dia)")
        meses_disp_caixa = sorted(df_all_proj['ano_mes'].unique(), reverse=True)
        mes_caixa_sel = st.selectbox("Selecione o Mês para ver o Caixa Diário:", meses_disp_caixa)
        
        df_caixa_mes = df_all_proj[df_all_proj['ano_mes'] == mes_caixa_sel].sort_values('data').copy()
        if not df_caixa_mes.empty:
            df_caixa_mes['valor_ajustado'] = df_caixa_mes.apply(lambda x: x['valor'] if x['tipo'] == 'Receita' else -x['valor'], axis=1)
            df_caixa_mes['Saldo Diário Acumulado'] = df_caixa_mes['valor_ajustado'].cumsum()
            df_graf_caixa = df_caixa_mes.set_index('data')[['Saldo Diário Acumulado']]
            st.line_chart(df_graf_caixa)
        
        st.markdown("---")
        st.subheader("🔮 Projeção de Longo Prazo")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            meses_proj = st.slider("Quantos meses deseja projetar?", min_value=1, max_value=12, value=6)
        with col_p2:
            aporte_extra_mensal = st.number_input("Previsão de Aporte/Economia Extra Mensal (R$):", min_value=0.0, value=0.00, step=50.0)

        resumo_meses = df_all_proj.pivot_table(index='ano_mes', columns='tipo', values='valor', aggfunc='sum').fillna(0)
        media_receitas = resumo_meses['Receita'].mean() if 'Receita' in resumo_meses.columns else 0.0
        media_despesas = resumo_meses['Despesa'].mean() if 'Despesa' in resumo_meses.columns else 0.0
        
        lista_projecao = []
        acumulado_proj = (resumo_meses['Receita'] - resumo_meses['Despesa']).sum() if 'Receita' in resumo_meses.columns else 0.0

        data_base = date.today()
        for i in range(1, meses_proj + 1):
            mes_futuro = data_base.month + i - 1
            ano_futuro = data_base.year + (mes_futuro // 12)
            mes_futuro = (mes_futuro % 12) + 1
            nome_mes_ano = f"{ano_futuro}-{mes_futuro:02d}"
            
            sobra_mes = (media_receitas - media_despesas) + aporte_extra_mensal
            acumulado_proj += sobra_mes
            
            lista_projecao.append({
                "Mês/Ano": nome_mes_ano,
                "Receita Projetada": media_receitas,
                "Despesa Projetada": media_despesas,
                "Aporte Extra": aporte_extra_mensal,
                "Patrimônio Acumulado Projetado": acumulado_proj
            })
            
        df_proj = pd.DataFrame(lista_projecao)
        st.dataframe(df_proj.style.format({
            'Receita Projetada': 'R$ {:,.2f}',
            'Despesa Projetada': 'R$ {:,.2f}',
            'Aporte Extra': 'R$ {:,.2f}',
            'Patrimônio Acumulado Projetado': 'R$ {:,.2f}'
        }), use_container_width=True)
        
        st.write("**Gráfico de Crescimento Patrimonial Projetado**")
        df_graf_proj = df_proj.set_index('Mês/Ano')[['Patrimônio Acumulado Projetado']]
        st.line_chart(df_graf_proj)
    else:
        st.info("Cadastre algumas transações para visualizar o fluxo de caixa e as projeções.")

# --- ABA 10: CONTAS A PAGAR ---
with aba10:
    st.subheader("📅 Calendário de Contas & Gerenciamento")
    
    with st.form("conta", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            venc = st.date_input("Data de Vencimento")
            nome_conta = st.text_input("Nome da Conta (Ex: IPVA, Seguro, Aluguel)")
        with col_c2:
            val_conta = st.number_input("Valor Estimado", min_value=0.0, value=0.00, step=1.0, format="%.2f")
        
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

# --- ABA 11: EXTRATO, IMPORTAÇÃO (CSV/PDF COM IA), EXPORTAÇÃO & BACKUP ---
with aba11:
    st.subheader("📋 Extrato Corporativo, Importação Inteligente (CSV / PDF) e Backup")
    
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        with open("gestor_financeiro.db", "rb") as f:
            st.download_button("💾 Baixar Backup do Banco (.db)", f, "gestor_financeiro.db", use_container_width=True)
    with col_exp2:
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
    
    st.write("### 📥 Importar Extrato Bancário com Categorização Automática (CSV ou PDF)")
    st.info("Faça o upload do extrato em **CSV** ou **PDF** (ex: Itaú). O app identificará os lançamentos (ignorando saldos diários) e categorizará automaticamente.")
    
    arquivo_importado = st.file_uploader("Escolha o arquivo do banco", type=["csv", "pdf"])
    
    if arquivo_importado is not None:
        extensao = arquivo_importado.name.split('.')[-1].lower()
        
        if extensao == "csv":
            try:
                df_imp = pd.read_csv(arquivo_importado)
                st.write("Pré-visualização do CSV:")
                st.dataframe(df_imp.head(3), use_container_width=True)
                
                col_data = st.selectbox("Coluna da Data:", df_imp.columns, key="csv_data")
                col_desc = st.selectbox("Coluna da Descrição:", df_imp.columns, key="csv_desc")
                col_val = st.selectbox("Coluna do Valor:", df_imp.columns, key="csv_val")
                
                if st.button("Confirmar e Importar CSV", use_container_width=True):
                    importados_contador = 0
                    for _, row in df_imp.iterrows():
                        try:
                            data_str = str(row[col_data])[:10]
                            desc_str = str(row[col_desc])
                            val_float = float(row[col_val])
                            
                            tipo_trans = "Receita" if val_float > 0 else "Despesa"
                            val_absoluto = abs(val_float)
                            cat_inteligente = categorizar_automaticamente(desc_str, tipo_trans)
                            
                            c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                                      (data_str, tipo_trans, desc_str, cat_inteligente, val_absoluto))
                            importados_contador += 1
                        except Exception:
                            continue
                    conn.commit()
                    st.success(f"{importados_contador} transações importadas do CSV com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao ler o CSV: {e}")
                
        elif extensao == "pdf":
            try:
                st.write("📄 Lendo o conteúdo do PDF do Itaú...")
                texto_pdf = ""
                with pdfplumber.open(arquivo_importado) as pdf:
                    for pagina in pdf.pages:
                        extraido = pagina.extract_text()
                        if extraido:
                            texto_pdf += extraido + "\n"
                
                st.text_area("Texto extraído do PDF (Pré-visualização):", texto_pdf[:1500], height=200)
                
                if st.button("Processar e Importar PDF do Itaú (Com Filtro de Saldo)", use_container_width=True):
                    linhas = texto_pdf.split("\n")
                    importados_pdf = 0
                    data_recente = date.today().strftime("%Y-%m-%d")
                    
                    for linha in linhas:
                        linha_upper = linha.upper()
                        # FILTRO CRUCIAL: Ignora linhas que contenham "SALDO" (como "SALDO DO DIA")
                        if "SALDO" in linha_upper:
                            continue
                            
                        partes = linha.split()
                        if len(partes) >= 3 and "/" in partes[0] and len(partes[0]) == 10:
                            try:
                                d_partes = partes[0].split('/')
                                if len(d_partes) == 3:
                                    data_recente = f"{d_partes[2]}-{d_partes[1]}-{d_partes[0]}"
                                
                                linha_limpa = linha.replace("R$", "").replace(".", "").replace(",", ".")
                                sub_partes = linha_limpa.split()
                                
                                val_str = sub_partes[-1]
                                val_float = float(val_str)
                                
                                desc_str = " ".join(partes[1:-1]) if len(partes) > 2 else "Lançamento Extrato"
                                
                                tipo_trans = "Receita" if val_float > 0 else "Despesa"
                                val_absoluto = abs(val_float)
                                
                                # Aplicação da Categorização Automática Inteligente
                                cat_inteligente = categorizar_automaticamente(desc_str, tipo_trans)
                                
                                c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                                          (data_recente, tipo_trans, desc_str, cat_inteligente, val_absoluto))
                                importados_pdf += 1
                            except Exception:
                                continue
                    
                    conn.commit()
                    st.success(f"{importados_pdf} lançamentos do PDF extraídos e categorizados com sucesso (saldos ignorados)!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o PDF: {e}")

    st.markdown("---")
    
    df_extrato_full = pd.read_sql("SELECT * FROM transacoes", conn)
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
