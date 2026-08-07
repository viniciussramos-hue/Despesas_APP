import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import io

st.set_page_config(page_title="💸 Controle de Entradas e Despesas", layout="centered")

# --- ARQUIVO PARA SALVAR OS DADOS NA MEMÓRIA ---
ARQUIVO_DADOS = "dados_despesas.json"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "orcamento_mes": 2000.0,
        "transacoes": []
    }

def salvar_dados():
    dados = {
        "orcamento_mes": st.session_state.get("orcamento_mes", 2000.0),
        "transacoes": st.session_state.transacoes
    }
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# --- ESTADO DA APLICAÇÃO ---
dados_salvos = carregar_dados()

if 'transacoes' not in st.session_state:
    st.session_state.transacoes = dados_salvos["transacoes"]

# Título do Aplicativo
st.title("💸 Controle de Entradas e Despesas")

# --- BARRA LATERAL: CONFIGURAÇÕES ---
with st.sidebar:
    st.header("⚙️ Configurações")
    orcamento_mes = st.number_input(
        "Orçamento Mensal (R$):", 
        min_value=0.0, 
        format="%.2f", 
        value=float(dados_salvos.get("orcamento_mes", 2000.0)),
        key="orcamento_mes",
        on_change=salvar_dados
    )
    st.divider()
    st.write("💡 **Dica:** Lance suas Receitas e Despesas para acompanhar o saldo em caixa e projeções.")

mapa_numeros = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10
}

def categorizar_transacao(nome, tipo):
    nome_lower = nome.lower()
    if tipo == "🟢 Receita":
        if any(k in nome_lower for k in ["salario", "pagamento", "pix", "freela", "renda", "venda"]):
            return "💰 Salário / Renda"
        return "📈 Outras Receitas"
    else:
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
aba_lancar, aba_dashboard, aba_extrato = st.tabs(["➕ Lançar Movimento", "📊 Dashboard", "📋 Extrato & Planilha"])

with aba_lancar:
    st.subheader("Adicionar Nova Entrada ou Saída")
    st.write("Digite ou fale (usando o microfone do teclado). Ex: `salario 3500` ou `almoço 35.00`")

    with st.form("form_transacao", clear_on_submit=True):
        tipo_movimento = st.radio("Tipo de Lançamento:", ["🔴 Despesa (Saída)", "🟢 Receita (Entrada)"], horizontal=True)
        entrada_texto = st.text_input("Descrição e Valor:", placeholder="Ex: almoço 35.00 ou salario 3500")
        btn_lancar = st.form_submit_button("➕ Registrar Movimento", use_container_width=True)

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
                nome_detectado = "Diversos"
                
            if numeros_encontrados:
                valor = numeros_encontrados[-1]
            else:
                raise Exception("Valor não encontrado")
                
            tipo_cat = "🟢 Receita" if "Receita" in tipo_movimento else "🔴 Despesa"
            categoria = categorizar_transacao(nome_detectado, tipo_cat)
            data_atual = datetime.now().strftime("%d/%m/%Y")
            
            st.session_state.transacoes.append({
                "data": data_atual,
                "tipo": tipo_cat,
                "descricao": nome_detectado,
                "categoria": categoria,
                "valor": valor
            })
            
            salvar_dados()
            st.success(f"Registrado com sucesso: {nome_detectado} - R$ {valor:.2f}")
            st.rerun()
                
        except Exception:
            st.warning("⚠️ Formato não reconhecido. Use o formato: `[Descrição] [Valor]` (Ex: `almoço 35.00`)")

    if st.session_state.transacoes:
        st.markdown("---")
        st.write("📌 **Últimos lançamentos:**")
        df_recentes = pd.DataFrame(st.session_state.transacoes).tail(3)
        for _, row in df_recentes.iterrows():
            st.write(f"• {row['data']} - {row['tipo']} - **{row['descricao']}** ({row['categoria']}) — R$ {row['valor']:.2f}")

with aba_dashboard:
    st.subheader("📊 Painel de Controle (Dashboard)")
    
    if st.session_state.transacoes:
        df = pd.DataFrame(st.session_state.transacoes)
        
        total_receitas = df[df["tipo"] == "🟢 Receita"]["valor"].sum()
        total_despesas = df[df["tipo"] == "🔴 Despesa"]["valor"].sum()
        saldo_caixa = total_receitas - total_despesas
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Receitas", f"R$ {total_receitas:.2f}")
        with col2:
            st.metric("Total Despesas", f"R$ {total_despesas:.2f}")
        with col3:
            st.metric("Saldo em Caixa", f"R$ {saldo_caixa:.2f}", delta=f"R$ {saldo_caixa:.2f}")

        st.markdown("---")
        
        # Projeção de gastos
        dia_hoje = datetime.now().day
        media_diaria = total_despesas / max(dia_hoje, 1)
        projecao_mes = media_diaria * 30
        
        if orcamento_mes > 0:
            if projecao_mes > orcamento_mes:
                st.error(f"⚠️ **Alerta de Projeção:** No ritmo atual, suas despesas fecharão o mês em **R$ {projecao_mes:.2f}**, ultrapassando o orçamento de R$ {orcamento_mes:.2f}!")
            else:
                st.success(f"✅ **Projeção Saudável:** Mantendo esse ritmo, suas despesas terminarão o mês em cerca de **R$ {projecao_mes:.2f}**, dentro do teto!")

        st.markdown("---")
        st.write("### 📈 Despesas Agrupadas por Categoria")
        df_despesas = df[df["tipo"] == "🔴 Despesa"]
        if not df_despesas.empty:
            df_cat = df_despesas.groupby("categoria")["valor"].sum()
            st.bar_chart(df_cat)
        else:
            st.info("Nenhuma despesa registrada ainda para gerar o gráfico.")
            
    else:
        st.info("Ainda não há dados suficientes para exibir o Dashboard. Registre entradas ou saídas na aba anterior!")

with aba_extrato:
    st.subheader("📋 Extrato Completo e Planilha")
    
    if st.session_state.transacoes:
        df = pd.DataFrame(st.session_state.transacoes)
        
        for idx, row in df.iterrows():
            col_d1, col_d2 = st.columns([4, 1])
            with col_d1:
                st.write(f"**{row['data']} - {row['tipo']} - [{row['categoria']}] {row['descricao']}** — **R$ {row['valor']:.2f}**")
            with col_d2:
                if st.button("❌", key=f"del_esp_{idx}"):
                    st.session_state.transacoes.pop(idx)
                    salvar_dados()
                    st.rerun()

        st.markdown("---")
        
        df_export = df.rename(columns={
            "data": "Data",
            "tipo": "Tipo",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "valor": "Valor (R$)"
        })
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📊 Baixar Relatório em Excel (CSV)",
            data=csv_data,
            file_name="controle_entradas_saidas.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.button("🗑️ Apagar Todos os Registros", use_container_width=True):
            st.session_state.transacoes = []
            salvar_dados()
            st.rerun()
    else:
        st.info("O extrato está vazio.")
