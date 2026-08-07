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
c.execute('''CREATE TABLE IF NOT EXISTS holerites 
             (id INTEGER PRIMARY KEY, mes_ano TEXT, salario_bruto REAL, total_descontos REAL, liquido REAL, inss REAL, irrf REAL)''')
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

# --- DEFINIÇÃO DAS ABAS (12 Abas) ---
aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10, aba11, aba12 = st.tabs([
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
    "📋 Extrato & Backup",
    "📄 Holerites"
])

# --- ABA 1: LANÇAR DESPESA ---
with aba1:
    st.subheader("Registrar Saída / Despesa")
    cats_padrao = [
        "🏠 Contas Fixas (Necessidade)", "🛒 Supermercado (Necessidade)", "🚗 Transporte (Necessidade)", 
        "💊 Saúde (Necessidade)", "🍔 Lazer & Alimentação Fora (Desejos)", "🎉 Outros Desejos (Desejos)", 
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

    if not df_all.empty and not df.empty:
        df_desp_all = df_all[df_all['tipo'] == 'Despesa']
        if len(df_desp_all['ano_mes'].unique()) > 1:
            media_por_cat = df_desp_all.groupby(['categoria', 'ano_mes'])['valor'].sum().reset_index()
            media_historica = media_por_cat.groupby('categoria')['valor'].mean().to_dict()
            gasto_atual_cat = df[df['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().to_dict()
            for cat, val in gasto_atual_cat.items():
                med = media_historica.get(cat, val)
                if med > 0 and val > (med * 1.3):
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
        total_contas_pendentes = df_contas[df_contas['pago'] == 0]['valor'].sum() if not df_contas.empty else 0

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
            meta_nec, meta_des, meta_inv = receitas * 0.50, receitas * 0.30, receitas * 0.20
            
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

        st.markdown("---")
        st.subheader("📈 Evolução e Saldo Acumulado Histórico")
        df_pivot = df_all.pivot_table(index='ano_mes', columns='tipo', values='valor', aggfunc='sum').fillna(0)
        if 'Receita' not in df_pivot.columns: df_pivot['Receita'] = 0
        if 'Despesa' not in df_pivot.columns: df_pivot['Despesa'] = 0
        df_pivot['Saldo Mensal'] = df_pivot['Receita'] - df_pivot['Despesa']
        df_pivot['Saldo Acumulado'] = df_pivot['Saldo Mensal'].cumsum()
        st.line_chart(df_pivot[['Saldo Acumulado']])
    else:
        st.info("Comece registrando transações para visualizar o dashboard.")

# --- ABA 4: CARTÃO DE CRÉDITO ---
with aba4:
    st.subheader("💳 Gestão Detalhada de Cartão de Crédito")
    with st.form("form_cartao", clear_on_submit=True):
        col_cc1, col_cc2 = st.columns(2)
        with col_cc1:
            nome_cartao = st.selectbox("Cartão", ["Itaúcard", "Samsung Itaú", "Nubank", "Outro"])
            desc_cc = st.text_input("Descrição da Compra")
        with col_cc2:
            val_cc = st.number_input("Valor da Compra (R$)", min_value=0.0, value=0.00, step=1.0, format="%.2f")
            data_cc = st.date_input("Data da Compra", value=date.today())
        cat_cc = st.selectbox("Categoria", ["🛒 Supermercado (Necessidade)", "🏠 Contas Fixas (Necessidade)", "🚗 Transporte (Necessidade)", "💊 Saúde (Necessidade)", "🍔 Lazer & Alimentação Fora (Desejos)"])
        if st.form_submit_button("Adicionar Gasto ao Cartão", use_container_width=True):
            c.execute("INSERT INTO cartao_credito (data, cartao, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data_cc.strftime("%Y-%m-%d"), nome_cartao, desc_cc, cat_cc, val_cc))
            conn.commit()
            st.success("Compra registrada com sucesso!")
            st.rerun()

    st.markdown("---")
    df_cartao = pd.read_sql("SELECT * FROM cartao_credito", conn)
    if not df_cartao.empty:
        st.dataframe(df_cartao, use_container_width=True)
        st.metric("💳 Total Acumulado em Faturas", f"R$ {df_cartao['valor'].sum():,.2f}")
        id_del_cc = st.selectbox("Selecione o ID da compra no cartão para remover:", df_cartao['id'].tolist())
        if st.button("Remover Compra Selecionada", use_container_width=True):
            c.execute("DELETE FROM cartao_credito WHERE id = ?", (id_del_cc,))
            conn.commit()
            st.success("Compra removida!")
            st.rerun()
    else:
        st.info("Nenhuma compra registrada nos cartões ainda.")

# --- ABA 5: INVESTIMENTOS ---
with aba5:
    st.subheader("📈 Dashboard Profissional de Investimentos & Carteira")
    with st.form("form_ativo_inv", clear_on_submit=True):
        col_iv1, col_iv2, col_iv3 = st.columns(3)
        with col_iv1:
            ativo_nome = st.text_input("Ativo / Ticker (Ex: PETR4)")
            classe_ativo = st.selectbox("Classe de Ativo", ["Ações BR", "FIIs", "Renda Fixa", "Criptomoedas", "Exterior"])
        with col_iv2:
            qtd_ativo = st.number_input("Quantidade / Cotas", min_value=0.0001, value=1.00, step=1.0)
            preco_medio = st.number_input("Preço Médio (R$)", min_value=0.0, value=0.00, step=0.10, format="%.2f")
        with col_iv3:
            data_aporte = st.date_input("Data do Aporte", value=date.today())
            st.write(""); st.write("")
            btn_add_ativo = st.form_submit_button("Cadastrar Posição", use_container_width=True)
        if btn_add_ativo and ativo_nome.strip():
            c.execute("INSERT INTO carteira_investimentos (data, ativo, classe, quantidade, preco_medio) VALUES (?,?,?,?,?)",
                      (data_aporte.strftime("%Y-%m-%d"), ativo_nome.upper().strip(), classe_ativo, qtd_ativo, preco_medio))
            conn.commit()
            st.success("Ativo cadastrado com sucesso!")
            st.rerun()

    df_carteira = pd.read_sql("SELECT * FROM carteira_investimentos", conn)
    if not df_carteira.empty:
        df_carteira['Valor Total'] = df_carteira['quantidade'] * df_carteira['preco_medio']
        st.metric("💎 Patrimônio Alocado", f"R$ {df_carteira['Valor Total'].sum():,.2f}")
        st.dataframe(df_carteira, use_container_width=True)

# --- ABA 6: DESAFIOS ---
with aba6:
    st.subheader("🎯 Desafio de Depósito (R$ 20.100,00 em 200 Depósitos)")
    df_deps = pd.read_sql("SELECT * FROM tabela_depositos", conn)
    total_concluido = df_deps[df_deps['status'] == 'Concluído']['valor'].sum()
    st.progress(min(total_concluido / 20100.0, 1.0))
    st.dataframe(df_deps, use_container_width=True)

# --- ABA 7: METAS & CATEGORIAS ---
with aba7:
    st.subheader("🎯 Gerenciamento de Metas, Ícones e Categorias")
    with st.form("form_meta", clear_on_submit=True):
        cat_meta = st.selectbox("Escolha a Categoria", ["🏠 Contas Fixas (Necessidade)", "🛒 Supermercado (Necessidade)", "🚗 Transporte (Necessidade)"])
        valor_meta_input = st.number_input("Valor Máximo de Meta (R$)", min_value=0.0, step=1.0, format="%.2f")
        if st.form_submit_button("Salvar Meta", use_container_width=True):
            c.execute("DELETE FROM metas WHERE categoria = ?", (cat_meta,))
            c.execute("INSERT INTO metas (categoria, valor_meta) VALUES (?, ?)", (cat_meta, valor_meta_input))
            conn.commit()
            st.success("Meta salva com sucesso!")
            st.rerun()

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

# --- ABA 9: PROJEÇÃO & CAIXA ---
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
            st.line_chart(df_caixa_mes.set_index('data')[['Saldo Diário Acumulado']])

# --- ABA 10: CONTAS A PAGAR ---
with aba10:
    st.subheader("📅 Calendário de Contas & Gerenciamento")
    with aba10_form := st.form("conta", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            venc = st.date_input("Data de Vencimento")
            nome_conta = st.text_input("Nome da Conta")
        with col_c2:
            val_conta = st.number_input("Valor Estimado", min_value=0.0, format="%.2f")
        if st.form_submit_button("Adicionar ao Calendário", use_container_width=True):
            c.execute("INSERT INTO contas (vencimento, descricao, valor, pago) VALUES (?,?,?,?)", (venc, str(nome_conta), val_conta, 0))
            conn.commit()
            st.success("Conta adicionada!")
            st.rerun()
            
    contas = pd.read_sql("SELECT * FROM contas", conn)
    if not contas.empty:
        st.dataframe(contas, use_container_width=True)

# --- ABA 11: EXTRATO & BACKUP ---
with aba11:
    st.subheader("📋 Extrato Corporativo, Importação Inteligente (CSV / PDF) e Backup")
    arquivo_importado = st.file_uploader("Escolha o arquivo do banco", type=["csv", "pdf"])
    if arquivo_importado is not None and arquivo_importado.name.endswith('.pdf'):
        with pdfplumber.open(arquivo_importado) as pdf:
            texto_pdf = "".join([p.extract_text() + "\n" for p in pdf.pages if p.extract_text()])
        if st.button("Processar e Importar PDF do Itaú (Com Filtro de Saldo)", use_container_width=True):
            importados_pdf = 0
            for linha in texto_pdf.split("\n"):
                if "SALDO" in linha.upper(): continue
                partes = linha.split()
                if len(partes) >= 3 and "/" in partes[0] and len(partes[0]) == 10:
                    try:
                        d = partes[0].split('/')
                        data_str = f"{d[2]}-{d[1]}-{d[0]}"
                        val_float = float(linha.replace("R$", "").replace(".", "").replace(",", ".").split()[-1])
                        tipo_trans = "Receita" if val_float > 0 else "Despesa"
                        desc_str = " ".join(partes[1:-1])
                        cat_inteligente = categorizar_automaticamente(desc_str, tipo_trans)
                        c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                                  (data_str, tipo_trans, desc_str, cat_inteligente, abs(val_float)))
                        importados_pdf += 1
                    except: continue
            conn.commit()
            st.success(f"{importados_pdf} lançamentos do PDF importados com sucesso!")
            st.rerun()

    df_extrato_full = pd.read_sql("SELECT * FROM transacoes", conn)
    if not df_extrato_full.empty:
        st.dataframe(df_extrato_full, use_container_width=True)

# --- ABA 12: HOLERITES ---
with aba12:
    st.subheader("📄 Análise e Importação de Holerite via PDF")
    st.info("Faça o upload do PDF do seu holerite para preencher automaticamente os dados ou preencha manualmente abaixo.")
    
    pdf_holerite = st.file_uploader("Escolha o arquivo PDF do Holerite", type=["pdf"], key="upload_holerite")
    
    val_mes_ano = "07/2026"
    val_bruto = 7440.65
    val_descontos = 6278.12
    val_liquido = 1162.53
    val_inss = 756.25
    val_irrf = 531.68
    
    if pdf_holerite is not None:
        try:
            texto_holerite = ""
            with pdfplumber.open(pdf_holerite) as pdf:
                for pagina in pdf.pages:
                    ext = pagina.extract_text()
                    if ext:
                        texto_holerite += ext + "\n"
            st.success("PDF do holerite lido com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler PDF do holerite: {e}")

    with st.form("form_holerite"):
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            mes_ano_hol = st.text_input("Mês/Ano", value=val_mes_ano)
            bruto_hol = st.number_input("Salário Bruto (R$)", min_value=0.0, value=float(val_bruto), format="%.2f")
        with col_h2:
            desc_hol = st.number_input("Total de Descontos (R$)", min_value=0.0, value=float(val_descontos), format="%.2f")
            liquido_hol = st.number_input("Salário Líquido (R$)", min_value=0.0, value=float(val_liquido), format="%.2f")
        with col_h3:
            inss_hol = st.number_input("Desconto INSS (R$)", min_value=0.0, value=float(val_inss), format="%.2f")
            irrf_hol = st.number_input("Desconto IRRF (R$)", min_value=0.0, value=float(val_irrf), format="%.2f")
            
        if st.form_submit_button("Salvar Holerite no Histórico", use_container_width=True):
            if mes_ano_hol.strip():
                c.execute("INSERT INTO holerites (mes_ano, salario_bruto, total_descontos, liquido, inss, irrf) VALUES (?,?,?,?,?,?)",
                          (mes_ano_hol.strip(), bruto_hol, desc_hol, liquido_hol, inss_hol, irrf_hol))
                conn.commit()
                st.success("Holerite salvo com sucesso!")
                st.rerun()
            else:
                st.error("Informe o Mês/Ano.")

    st.markdown("---")
    df_holerites = pd.read_sql("SELECT * FROM holerites", conn)
    if not df_holerites.empty:
        st.write("### 📋 Histórico de Holerites Cadastrados")
        st.dataframe(df_holerites.style.format({
            'salario_bruto': 'R$ {:,.2f}',
            'total_descontos': 'R$ {:,.2f}',
            'liquido': 'R$ {:,.2f}',
            'inss': 'R$ {:,.2f}',
            'irrf': 'R$ {:,.2f}'
        }), use_container_width=True)
        
        st.write("**Gráfico Comparativo: Bruto vs Líquido vs Descontos**")
        st.line_chart(df_holerites.set_index('mes_ano')[['salario_bruto', 'liquido', 'total_descontos']])
        
        id_del_hol = st.selectbox("Selecione o ID do holerite para remover:", df_holerites['id'].tolist(), key="del_hol")
        if st.button("Excluir Holerite Selecionado", use_container_width=True):
            c.execute("DELETE FROM holerites WHERE id = ?", (id_del_hol,))
            conn.commit()
            st.success("Holerite excluído!")
            st.rerun()
    else:
        st.info("Nenhum holerite cadastrado no histórico ainda.")
