from datetime import datetime, date
import io
import os
import sqlite3
import pandas as pd
import pdfplumber
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA (ESTILO 100% GESTORMONEY)
# ==========================================
st.set_page_config(
    page_title="GestorMoney - Seu Aliado Financeiro",
    page_icon="💰",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color: #0c101d; color: #e5e7eb; }
    .stSidebar { background-color: #121826; border-right: 1px solid #1f2937; }
    
    .gm-card {
        background-color: #161e2e;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #1f2937;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .gm-card-title {
        color: #9ca3af;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .gm-card-value {
        font-size: 24px;
        font-weight: 700;
        margin: 8px 0;
    }
    .gm-card-footer {
        color: #6b7280;
        font-size: 11px;
    }
    h1, h2, h3 { color: #f9fafb !important; }
    
    .btn-verde button {
        background-color: #a3e635 !important;
        color: #000 !important;
        font-weight: bold !important;
        border: none !important;
    }
    .btn-verde button:hover {
        background-color: #bef264 !important;
        color: #000 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# BANCO DE DADOS E MIGRATIONS (SQLite)
# ==========================================
DB_NAME = "gestormoney_original.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            descricao TEXT,
            valor REAL,
            tipo TEXT,
            categoria TEXT,
            observacoes TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            tipo TEXT,
            icone TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT,
            total_investido REAL,
            valor_mercado REAL
        )
    """)

  cursor.execute("SELECT COUNT(*) FROM categorias")
  if cursor.fetchone()[0] == 0:
    categorias_iniciais = [
        ("Alimentação", "Despesa", "🍔"),
        ("Supermercado", "Despesa", "🛒"),
        ("Moradia / Aluguel", "Despesa", "🏠"),
        ("Contas e Boletos", "Despesa", "💡"),
        ("Transporte", "Despesa", "🚗"),
        ("Combustível", "Despesa", "⛽"),
        ("Saúde / Farmácia", "Despesa", "💊"),
        ("Educação", "Despesa", "📚"),
        ("Lazer / Entretenimento", "Despesa", "🎮"),
        ("Vestuário", "Despesa", "👕"),
        ("Pets", "Despesa", "🐾"),
        ("Assinaturas e Serviços", "Despesa", "📱"),
        ("Outras Despesas", "Despesa", "📦"),
        ("Salário", "Receita", "💵"),
        ("Freelance", "Receita", "💻"),
        ("Investimentos", "Receita", "📈"),
        ("Outras Receitas", "Receita", "💰"),
    ]
    cursor.executemany(
        "INSERT INTO categorias (nome, tipo, icone) VALUES (?, ?, ?)",
        categorias_iniciais,
    )

  conn.commit()
  conn.close()


init_db()


# ==========================================
# RECONHECIMENTO AUTOMÁTICO DE CATEGORIA
# ==========================================
def categorizar_automaticamente(descricao, valor):
  desc = descricao.upper()
  if valor > 0:
    if any(
        k in desc for k in ["SALARIO", "REMUNERACAO", "PRO-LABORE", "FOLHA"]
    ):
      return "Salário"
    if any(k in desc for k in ["FREELANC", "PRESTACAO", "SERVICO"]):
      return "Freelance"
    if any(k in desc for k in ["DIVIDENDOS", "RENDIMENTO", "JUROS SOBRE"]):
      return "Investimentos"
    return "Outras Receitas"
  else:
    if any(
        k in desc for k in ["SUPERMERCADO", "MERCADO", "HIPER", "ATACAD"]
    ):
      return "Supermercado"
    if any(k in desc for k in ["RESTAURANTE", "IFOOD", "LANCHONETE", "PADARIA"]):
      return "Alimentação"
    if any(k in desc for k in ["POSTO", "COMBUSTIVEL", "SHELL", "PETROBRAS"]):
      return "Combustível"
    if any(k in desc for k in ["UBER", "99APP", "ESTACIONAMENTO", "PEDAGIO"]):
      return "Transporte"
    if any(k in desc for k in ["FARMACIA", "DROGARIA", "HOSPITAL", "CLINICA"]):
      return "Saúde / Farmácia"
    if any(k in desc for k in ["LUZ", "AGUA", "TELEFONE", "INTERNET", "NETFLIX"]):
      return "Contas e Boletos"
    return "Outras Despesas"


def obter_icone(categoria):
  conn = sqlite3.connect(DB_NAME)
  res = conn.execute(
      "SELECT icone FROM categorias WHERE nome = ?", (categoria,)
  ).fetchone()
  conn.close()
  return res[0] if res else "📁"


# ==========================================
# MENU LATERAL
# ==========================================
st.sidebar.markdown(
    """
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
        <div style='background: #f59e0b; padding: 8px; border-radius: 8px; font-weight: bold; color: #000;'>🤖</div>
        <div>
            <span style='font-size: 16px; font-weight: bold; color: #fff;'>GestorMoney</span><br>
            <span style='font-size: 11px; color: #9ca3af;'>SEU ALIADO FINANCEIRO</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<p style='color: #9ca3af; font-size: 12px; margin-bottom: 10px;'>"
    "Navegação Principal</p>",
    unsafe_allow_html=True,
)

if "menu_ativo" not in st.session_state:
  st.session_state["menu_ativo"] = "Dashboard"

if st.sidebar.button(
    "📊 Dashboard",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Dashboard"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Dashboard"
  st.rerun()

if st.sidebar.button(
    "📂 Importar Extrato",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Importar Extrato"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Importar Extrato"
  st.rerun()

if st.sidebar.button(
    "🔄 Transações",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Transações"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Transações"
  st.rerun()

if st.sidebar.button(
    "📁 Categorias",
    use_container_width=True,
    type="primary"
    if st.session_state["menu_ativo"] == "Categorias"
    else "secondary",
):
  st.session_state["menu_ativo"] = "Categorias"
  st.rerun()

menu = st.session_state["menu_ativo"]
conn = sqlite3.connect(DB_NAME)

# ==========================================
# MÓDULO: DASHBOARD
# ==========================================
if menu == "Dashboard":
  col_head1, col_head2 = st.columns([3, 1])
  with col_head1:
    st.markdown(
        "<h1 style='margin-bottom: 0;'>Dashboard</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color: #9ca3af; margin-top: 0;'>Bem-vindo de volta,"
        " Vinicius Ramos</p>",
        unsafe_allow_html=True,
    )
  with col_head2:
    st.markdown(
        """
        <div style='background-color: #161e2e; border: 1px solid #1f2937; padding: 8px 15px; border-radius: 20px; text-align: right; display: flex; align-items: center; justify-content: flex-end; gap: 10px;'>
            <span style='color: #f59e0b; font-weight: bold;'>❤️ 375</span>
            <span style='background: #10b981; color: #000; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;'>Atenção</span>
            <span style='background: #374151; color: #fff; padding: 4px 8px; border-radius: 50%; font-size: 11px; font-weight: bold;'>VR</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown(
      """
      <div style='background-color: #161e2e; border: 1px solid #1f2937; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; font-size: 14px;'>
          <span style='color: #f59e0b; font-weight: bold;'>🏆 0/9</span>
          <span style='color: #6b7280;'>|</span>
          <span>🎯 🪙 🛡️ 📊 💡 🚀 👑 ⚡ ❓</span>
      </div>
  """,
      unsafe_allow_html=True,
  )

  df_trans = pd.read_sql("SELECT * FROM transacoes", conn)
  df_inv = pd.read_sql("SELECT * FROM investimentos", conn)

  total_receitas = (
      df_trans[df_trans["tipo"] == "Receita"]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  total_despesas = (
      df_trans[df_trans["tipo"] == "Despesa"]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  saldo_caixa = total_receitas - total_despesas

  total_investido = (
      df_inv["total_investido"].sum() if not df_inv.empty else 0.0
  )
  valor_mercado = df_inv["valor_mercado"].sum() if not df_inv.empty else 0.0
  lucro_inv = valor_mercado - total_investido
  patrimonio_total = total_investido + saldo_caixa

  col_c1, col_c2 = st.columns(2)
  with col_c1:
    st.markdown(
        f"""
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="gm-card-title">💰 Disponível em Caixa ℹ️</span>
                <span style="color: #10b981; font-size: 16px;">👁️</span>
            </div>
            <div class="gm-card-value" style="color: #10b981;">R$ {saldo_caixa:,.2f}</div>
            <div class="gm-card-footer">Patrimônio inicial<br>Saldo (receitas – despesas): R$ {saldo_caixa:,.2f}</div>
            <div style="margin-top: 15px; font-size: 13px; color: #e5e7eb; display: flex; justify-content: space-between; border-top: 1px solid #1f2937; padding-top: 10px;">
                <span>✨ Previsão fim do mês</span>
                <b style="color: #3b82f6;">R$ {saldo_caixa:,.2f} ▾</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with col_c2:
    st.markdown(
        f"""
        <div class="gm-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="gm-card-title">📈 Investimentos ℹ️</span>
                <span style="color: #10b981; font-size: 16px;">📈</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                <div>
                    <span style="color: #6b7280; font-size: 11px;">Total Investido</span><br>
                    <b style="font-size: 15px;">R$ {total_investido:,.2f}</b>
                </div>
                <div>
                    <span style="color: #6b7280; font-size: 11px;">Valor de Mercado</span><br>
                    <b style="font-size: 15px;">R$ {valor_mercado:,.2f}</b>
                </div>
                <div>
                    <span style="color: #6b7280; font-size: 11px;">Lucro</span><br>
                    <b style="font-size: 15px; color: #10b981;">+R$ {lucro_inv:,.2f}</b>
                </div>
            </div>
            <div style="margin-top: 15px; font-size: 13px; color: #e5e7eb; display: flex; justify-content: space-between; border-top: 1px solid #1f2937; padding-top: 10px;">
                <span>Patrimônio Total<br><span style="color: #6b7280; font-size: 11px;">Caixa + investimentos</span></span>
                <b style="font-size: 18px; color: #10b981;">R$ {patrimonio_total:,.2f}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  dc1, dc2, dc3, dc4 = st.columns(4)
  with dc1:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">📉 Dívida Total ℹ️</div>
            <div class="gm-card-value" style="color: #ef4444;">R$ 0,00</div>
            <div class="gm-card-footer">Cartões + contas + financiamentos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc2:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">↗️ Contas a Receber Este Mês ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">R$ {total_receitas:,.2f}</div>
            <div class="gm-card-footer">Vencimentos do mês</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc3:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">📅 Contas a Pagar Este Mês ℹ️</div>
            <div class="gm-card-value" style="color: #f59e0b;">R$ {total_despesas:,.2f}</div>
            <div class="gm-card-footer">Cartões + contas + dívidas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with dc4:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">💳 Limite Disponível Cartões ℹ️</div>
            <div class="gm-card-value" style="color: #3b82f6;">R$ 0,00</div>
            <div class="gm-card-footer">Limite total: R$ 0,00</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.divider()

  gc1, gc2 = st.columns(2)
  with gc1:
    st.subheader("Fluxo de Caixa Pessoal")
    if not df_trans.empty:
      st.bar_chart(df_trans.groupby("tipo")["valor"].sum())
    else:
      st.info("Sem dados.")

  with gc2:
    st.subheader("Comparativo por Categoria")
    if not df_trans.empty:
      st.bar_chart(df_trans.groupby("categoria")["valor"].sum())
    else:
      st.info("Sem dados.")

  st.divider()

  pc1, pc2, pc3, pc4 = st.columns(4)
  with pc1:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">Saldo do Período ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">R$ {saldo_caixa:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with pc2:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">Receitas ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">R$ {total_receitas:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with pc3:
    st.markdown(
        f"""
        <div class="gm-card">
            <div class="gm-card-title">Despesas ℹ️</div>
            <div class="gm-card-value" style="color: #ef4444;">R$ {total_despesas:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with pc4:
    st.markdown(
        """
        <div class="gm-card">
            <div class="gm-card-title">Saúde Financeira ℹ️</div>
            <div class="gm-card-value" style="color: #10b981;">100%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown(
      """
      <div class="gm-card">
          <b>Transações Recentes (Categorizadas Automaticamente)</b>
      """,
      unsafe_allow_html=True,
  )

  if not df_trans.empty:
    df_recentes = df_trans.tail(10).iloc[::-1].copy()
    df_recentes["Ícone"] = df_recentes["categoria"].apply(obter_icone)
    st.dataframe(
        df_recentes[[
            "data",
            "Ícone",
            "descricao",
            "categoria",
            "tipo",
            "valor",
            "observacoes",
        ]],
        use_container_width=True,
    )
  else:
    st.markdown(
        "<div style='text-align: center; padding: 20px; color:"
        " #6b7280;'>Nenhuma transação recente.</div>",
        unsafe_allow_html=True,
    )
  st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# MÓDULO: IMPORTAR EXTRATO (COM AUTO-CATEGORIZAÇÃO)
# ==========================================
elif menu == "Importar Extrato":
  st.markdown("<h1>📂 Importar Extrato Bancário</h1>", unsafe_allow_html=True)
  st.markdown(
      "<p style='color: #9ca3af;'>Faça upload do extrato (CSV ou PDF). As"
      " categorias serão reconhecidas <b>automaticamente</b> pela"
      " descrição.</p>",
      unsafe_allow_html=True,
  )

  uploaded_file = st.file_uploader(
      "Escolha o arquivo de extrato", type=["csv", "txt", "pdf"]
  )

  if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()

    if file_extension in ["csv", "txt"]:
      try:
        df_importado = pd.read_csv(uploaded_file)
        st.success("CSV carregado!")
        cols_disp = df_importado.columns.tolist()
        c1, c2, c3 = st.columns(3)
        with c1:
          col_data = st.selectbox("Coluna de Data", cols_disp)
        with c2:
          col_desc = st.selectbox("Coluna de Descrição", cols_disp)
        with c3:
          col_valor = st.selectbox("Coluna de Valor", cols_disp)

        if st.button(
            "📥 Processar e Categorizar Automaticamente",
            type="primary",
            use_container_width=True,
        ):
          cursor = conn.cursor()
          count = 0
          for _, row in df_importado.iterrows():
            data_val = str(row[col_data])
            desc_val = str(row[col_desc])
            try:
              valor_val = float(
                  str(row[col_valor])
                  .replace("R$", "")
                  .replace(".", "")
                  .replace(",", ".")
                  .strip()
              )
            except:
              valor_val = 0.0

            tipo_val = "Receita" if valor_val > 0 else "Despesa"
            valor_val = abs(valor_val)

            # Auto-categoria baseada na descrição
            cat_auto = categorizar_automaticamente(desc_val, valor_val)

            cursor.execute(
                """
                        INSERT INTO transacoes (data, descricao, valor, tipo, categoria, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                (
                    data_val,
                    desc_val,
                    valor_val,
                    tipo_val,
                    cat_auto,
                    "Importado via CSV",
                ),
            )
            count += 1
          conn.commit()
          st.success(
              f"🎉 {count} transações importadas e categorizadas automaticamente!"
          )
      except Exception as e:
        st.error(f"Erro: {e}")

    elif file_extension == "pdf":
      try:
        with pdfplumber.open(uploaded_file) as pdf:
          texto_extraido = ""
          for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
              texto_extraido += t + "\n"

        st.success("📄 PDF lido com sucesso!")

        if st.button(
            "📥 Processar e Categorizar Automaticamente o PDF",
            type="primary",
            use_container_width=True,
        ):
          cursor = conn.cursor()
          linhas = texto_extraido.split("\n")
          count = 0
          for linha in linhas:
            if "R$" in linha or any(char.isdigit() for char in linha):
              partes = linha.split()
              if len(partes) >= 2:
                descricao = " ".join(partes[:-1])
                try:
                  val_str = (
                      partes[-1]
                      .replace("R$", "")
                      .replace(".", "")
                      .replace(",", ".")
                  )
                  valor = float(val_str)
                  tipo = "Receita" if valor > 0 else "Despesa"
                  valor = abs(valor)
                  data_hoje = datetime.today().strftime("%Y-%m-%d")

                  # Auto-categoria baseada na descrição
                  cat_auto = categorizar_automaticamente(descricao, valor)

                  cursor.execute(
                      """
                                    INSERT INTO transacoes (data, descricao, valor, tipo, categoria, observacoes)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """,
                      (
                          data_hoje,
                          descricao,
                          valor,
                          tipo,
                          cat_auto,
                          "Importado via PDF",
                      ),
                  )
                  count += 1
                except:
                  continue

          conn.commit()
          st.success(
              f"🎉 {count} transações do PDF extraídas e categorizadas"
              " automaticamente!"
          )
      except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")


# ==========================================
# MÓDULO: TRANSAÇÕES
# ==========================================
elif menu == "Transações":
  st.markdown("<h1>🔄 Transações</h1>", unsafe_allow_html=True)
  df_trans = pd.read_sql("SELECT * FROM transacoes", conn)

  if not df_trans.empty:
    df_trans["Ícone"] = df_trans["categoria"].apply(obter_icone)
    st.dataframe(
        df_trans[[
            "id",
            "data",
            "Ícone",
            "descricao",
            "categoria",
            "tipo",
            "valor",
            "observacoes",
        ]],
        use_container_width=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🗑️ Excluir Transação Lançada Errada"):
      id_exc = st.number_input(
          "Informe o ID da transação para remover",
          min_value=1,
          step=1,
          format="%d",
      )
      if st.button("Confirmar Exclusão", type="primary"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transacoes WHERE id = ?", (id_exc,))
        conn.commit()
        st.success("Transação excluída com sucesso!")
        st.rerun()
  else:
    st.info("Nenhuma transação cadastrada.")


# ==========================================
# MÓDULO: CATEGORIAS
# ==========================================
elif menu == "Categorias":
  c_t1, c_t2 = st.columns([3, 1])
  with c_t1:
    st.markdown(
        "<h1 style='margin-bottom: 0;'>Categorias</h1>", unsafe_allow_html=True
    )
  with c_t2:
    st.markdown('<div class="btn-verde">', unsafe_allow_html=True)
    nova_cat_btn = st.button("＋ Nova Categoria", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

  df_categorias = pd.read_sql("SELECT * FROM categorias", conn)
  if df_categorias.empty:
    st.info("Nenhuma categoria encontrada.")
  else:
    for i in range(0, len(df_categorias), 4):
      subset = df_categorias.iloc[i : i + 4]
      cols = st.columns(4)
      for idx, (_, row) in enumerate(subset.iterrows()):
        with cols[idx]:
          cor = "#10b981" if row["tipo"] == "Receita" else "#ef4444"
          st.markdown(
              f"""
                <div class="gm-card" style="padding: 15px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{row['icone']}</span>
                        <span style="color: {cor}; font-size: 10px; font-weight: bold;">{row['tipo']}</span>
                    </div>
                    <div style="font-weight: bold; margin-top: 10px; color: #fff;">{row['nome']}</div>
                </div>
                """,
              unsafe_allow_html=True,
          )

conn.close()
