import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="💸 Controle Diário de Despesas", layout="centered")

# --- ESTADO DA APLICAÇÃO ---
if 'despesas' not in st.session_state:
    st.session_state.despesas = []

# Título do Aplicativo
st.title("💸 Controle Diário de Despesas")

# --- BARRA LATERAL: ORÇAMENTO ---
with st.sidebar:
    st.header("⚙️ Configurações")
    orcamento_mes = st.number_input("Orçamento Mensal (R$):", min_value=0.0, format="%.2f", value=2000.0)
    st.divider()
    st.write("💡 **Dica:** O Dashboard calcula automaticamente suas projeções e médias com base nos lançamentos.")

mapa_numeros = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10
}

def categorizar_gasto(nome):
    nome_lower = nome.lower()
    if any(k in nome_lower for k in ["almoço", "jantar", "lanche", "mercado", "padaria", "cafe", "restaurante", "pizza"]):
        return "🍔 Alimentação"
    elif any(k in nome_lower for k in ["uber", "taxi", "gasolina", "onibus", "metro", "pedagio", "estacionamento"]):
        return "🚗 Transporte"
    elif any(k in nome_lower for k in ["luz", "agua", "internet", "aluguel", "gas", "condominio"]):
        return "🏠 Contas Fixas"
    elif any(k in nome_lower for k in ["farmacia", "remedio", "medico", "hospital"]):
        return "💊 Saúde"
    elif any(k in nome_lower for k in ["cinema", "passeio", "cerveja", "jogo", "viagem"]):
        return "🎉 Lazer"
    else:
        return "📦 Outros"

# --- ABAS DA APLICAÇÃO ---
aba_lancar, aba_dashboard, aba_extrato = st.tabs(["➕ Lançar Gasto", "📊 Dashboard", "📋 Extrato & Planilha"])

with aba_lancar:
    st.subheader("Adicionar Novo Gasto")
    st.write("Digite ou fale (usando o microfone do teclado). Ex: `almoço 35.00` ou `uber 20`")

    with st.form("form_despesa", clear_on_submit=True):
        entrada_texto = st.text_input("Descrição e Valor:", placeholder="Ex: almoço 35.00")
        btn_lancar = st.form_submit_button("➕ Registrar Gasto", use_container_width=True)

    if btn_lancar and entrada_texto:
        texto_limpo = entrada_texto.lower()
        for termo in ["reais", "real", "r$"]:
            texto_limpo = texto_limpo.replace(termo, "")
            
        partes = texto_limpo.strip().split()
        
        try:
            numeros_encontrados = []
            palavras_nome = []
            
            for p in partes:
                p_limpo = p.replace(',', '.')
                if p_limpo.replace('.', '', 1).isdigit() or p in mapa_numeros:
                    val = float(mapa_numeros[p]) if p in mapa_numeros else float(p_limpo)
                    numeros_encontrados.append(val)
                else:
                    palavras_nome.append(p)
                    
            nome_bruto = " ".join(palavras_nome).strip()
            nome_detectado = " ".join([w.capitalize() for w in nome_bruto.split()])
            if not nome_detectado:
                nome_detectado = "Gasto Diversos"
                
            if numeros_encontrados:
                valor = numeros_encontrados[-1]
            else:
                raise Exception("Valor não encontrado")
                
            categoria = categorizar_gasto(nome_detectado)
            data_atual = datetime.now().strftime("%d/%m/%Y")
            
            st.session_state.despesas.append({
                "data": data_atual,
                "descricao": nome_detectado,
                "categoria": categoria,
                "valor": valor
            })
            
            st.success(f"Registrado com sucesso: {nome_detectado} - R$ {valor:.2f}")
            st.rerun()
            
        except Exception:
            st.warning("⚠️ Formato não reconhecido. Use o formato: `[Descrição] [Valor]` (Ex: `almoço 35.00`)")

    if st.session_state.despesas:
        st.markdown("---")
        st.write("📌 **Últimos lançamentos:**")
        df_recentes = pd.DataFrame(st.session_state.despesas).tail(3)
        for _, row in df_recentes.iterrows():
            st.write(f"• {row['data']} - **{row['descricao']}** ({row['categoria']}) — R$ {row['valor']:.2f}")

with aba_dashboard:
    st.subheader("📊 Painel de Controle (Dashboard)")
    
    if st.session_state.despesas:
        df = pd.DataFrame(st.session_state.despesas)
        total_gasto = df["valor"].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Gasto", f"R$ {total_gasto:.2f}")
        with col2:
            if orcamento_mes > 0:
                restante = orcamento_mes - total_gasto
                st.metric("Orçamento Restante", f"R$ {restante:.2f}")
        with col3:
            dia_hoje = datetime.now().day
            media_diaria = total_gasto / max(dia_hoje, 1)
            st.metric("Média por Dia", f"R$ {media_diaria:.2f}")

        projecao_mes = media_diaria * 30
        if orcamento_mes > 0:
            if projecao_mes > orcamento_mes:
                st.error(f"⚠️ **Alerta de Projeção:** No ritmo atual, você fechará o mês gastando **R$ {projecao_mes:.2f}**, ultrapassando o seu orçamento de R$ {orcamento_mes:.2f}!")
            else:
                st.success(f"✅ **Projeção Saudável:** Mantendo esse ritmo, você terminará o mês gastando cerca de **R$ {projecao_mes:.2f}**, dentro do seu teto!")

        st.markdown("---")
        st.write("### 📈 Gastos Agrupados por Categoria")
        df_cat = df.groupby("categoria")["valor"].sum()
        st.bar_chart(df_cat)
        
    else:
        st.info("Ainda não há dados suficientes para exibir o Dashboard. Registre alguns gastos na aba anterior!")

with aba_extrato:
    st.subheader("📋 Extrato Completo e Planilha")
    
    if st.session_state.despesas:
        df = pd.DataFrame(st.session_state.despesas)
        
        for idx, row in df.iterrows():
            col_d1, col_d2 = st.columns([4, 1])
            with col_d1:
                st.write(f"**{row['data']} - [{row['categoria']}] {row['descricao']}** — **R$ {row['valor']:.2f}**")
            with col_d2:
                if st.button("❌", key=f"del_esp_{idx}"):
                    st.session_state.despesas.pop(idx)
                    st.rerun()

        st.markdown("---")
        
        df_export = df.rename(columns={
            "data": "Data",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "valor": "Valor (R$)"
        })
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📊 Baixar Relatório em Excel (CSV)",
            data=csv_data,
            file_name="controle_despesas.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.button("🗑️ Apagar Todos os Registros", use_container_width=True):
            st.session_state.despesas = []
            st.rerun()
    else:
        st.info("O extrato está vazio.")
