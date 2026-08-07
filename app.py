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
        mes_selecionado = st.selectbox("Filtrar por Mês/Ano:", meses_disponiveis)
        df = df_all[df_all['ano_mes'] == mes_selecionado].copy()
    else:
        df = df_all.copy()

    if not df_all.empty:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        saldo_caixa = receitas - despesas
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Saldo do Período", f"R$ {saldo_caixa:,.2f}")
        col2.metric("🟢 Entradas", f"R$ {receitas:,.2f}")
        col3.metric("🔴 Despesas", f"R$ {despesas:,.2f}")
        
        st.markdown("---")
        df_pivot = df_all.pivot_table(index='ano_mes', columns='tipo', values='valor', aggfunc='sum').fillna(0)
        if 'Receita' not in df_pivot.columns: df_pivot['Receita'] = 0
        if 'Despesa' not in df_pivot.columns: df_pivot['Despesa'] = 0
        df_pivot['Saldo Acumulado'] = (df_pivot['Receita'] - df_pivot['Despesa']).cumsum()
        st.line_chart(df_pivot[['Saldo Acumulado']])
    else:
        st.info("Comece registrando transações.")

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
        cat_cc = st.selectbox("Categoria", ["🛒 Supermercado (Necessidade)", "🏠 Contas Fixas (Necessidade)"])
        if st.form_submit_button("Adicionar Gasto ao Cartão", use_container_width=True):
            c.execute("INSERT INTO cartao_credito (data, cartao, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                      (data_cc.strftime("%Y-%m-%d"), nome_cartao, desc_cc, cat_cc, val_cc))
            conn.commit()
            st.success("Compra registrada!")
            st.rerun()

    df_cartao = pd.read_sql("SELECT * FROM cartao_credito", conn)
    if not df_cartao.empty:
        st.dataframe(df_cartao, use_container_width=True)

# --- ABA 5: INVESTIMENTOS ---
with aba5:
    st.subheader("📈 Dashboard de Investimentos")
    df_carteira = pd.read_sql("SELECT * FROM carteira_investimentos", conn)
    if not df_carteira.empty:
        st.dataframe(df_carteira, use_container_width=True)

# --- ABA 6: DESAFIOS ---
with aba6:
    st.subheader("🎯 Desafio de Depósito")
    df_deps = pd.read_sql("SELECT * FROM tabela_depositos", conn)
    st.dataframe(df_deps, use_container_width=True)

# --- ABA 7: METAS & CATEGORIAS ---
with aba7:
    st.subheader("🎯 Metas & Categorias")
    df_metas = pd.read_sql("SELECT * FROM metas", conn)
    if not df_metas.empty:
        st.dataframe(df_metas, use_container_width=True)

# --- ABA 8: SAÚDE FINANCEIRA ---
with aba8:
    st.subheader("❤️ Saúde Financeira")
    st.info("Acompanhamento do score de saúde financeira.")

# --- ABA 9: PROJEÇÃO & CAIXA ---
with aba9:
    st.subheader("🔮 Projeção Financeira & Fluxo de Caixa")

# --- ABA 10: CONTAS A PAGAR ---
with aba10:
    st.subheader("📅 Contas a Pagar")
    contas = pd.read_sql("SELECT * FROM contas", conn)
    if not contas.empty:
        st.dataframe(contas, use_container_width=True)

# --- ABA 11: EXTRATO & BACKUP ---
with aba11:
    st.subheader("📋 Extrato & Importação PDF/CSV")
    arquivo_importado = st.file_uploader("Arquivo do Banco", type=["csv", "pdf"])
    if arquivo_importado is not None and arquivo_importado.name.endswith('.pdf'):
        with pdfplumber.open(arquivo_importado) as pdf:
            texto_pdf = "".join([p.extract_text() + "\n" for p in pdf.pages if p.extract_text()])
        if st.button("Processar PDF do Itaú", use_container_width=True):
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
                        c.execute("INSERT INTO transacoes (data, tipo, descricao, categoria, valor) VALUES (?,?,?,?,?)",
                                  (data_str, tipo_trans, " ".join(partes[1:-1]), categorizar_automaticamente(" ".join(partes[1:-1]), tipo_trans), abs(val_float)))
                        importados_pdf += 1
                    except: continue
            conn.commit()
            st.success(f"{importados_pdf} lançamentos importados!")
            st.rerun()

# --- ABA 12: HOLERITES & IMPORTAÇÃO DE PDF ---
with aba12:
    st.subheader("📄 Análise e Importação de Holerite via PDF")
    st.info("Faça o upload do PDF do seu holerite para preencher automaticamente os dados ou preencha manualmente abaixo.")
    
    # Upload do Holerite em PDF
    pdf_holerite = st.file_uploader("Escolha o arquivo PDF do Holerite", type=["pdf"], key="upload_holerite")
    
    # Valores padrão ou extraídos
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
            
            st.success("PDF do holerite lido com sucesso! Verifique os dados extraídos abaixo.")
            
            # Lógica simples de varredura para encontrar palavras-chave no texto do holerite (ex: Maxion / Iochpe)
            linhas_h = texto_holerite.split("\n")
            for linha in linhas_h:
                if "07/2026" in linha or "08/2026" in linha or "06/2026" in linha:
                    for p_L in linha.split():
                        if "/" in p_L and len(p_L) == 7:
                            val_mes_ano = p_L
                # Tenta pegar totais se identificados
                if "TOTAIS" in linha.upper():
                    partes_t = linha.replace(".", "").replace(",", ".").split()
                    nums_t = [float(x) for x in partes_t if x.replace('.', '', 1).isdigit()]
                    if len(nums_t) >= 2:
                        val_bruto = nums_t[0]
                        val_descontos = nums_t[1]
                if "LÍQUIDO:" in linha.upper() or "LIQUIDO:" in linha.upper():
                    partes_l = linha.replace(".", "").replace(",", ".").split()
                    for item in partes_l:
                        try:
                            v_cand = float(item)
                            if v_cand > 0 and v_cand != val_bruto:
                                val_liquido = v_cand
                        except:
                            continue
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
