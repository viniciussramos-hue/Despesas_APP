elif pagina == "📥 Dashboard Banco":
    botao_voltar()
    st.subheader("📥 Dashboard de Auditoria & Extratos Importados do Banco")
    st.write("Painel exclusivo para analisar transações geradas automaticamente por upload de extratos bancários em PDF.")

    df_banco_all = pd.read_sql("SELECT * FROM transacoes WHERE origem = 'Banco_PDF'", conn)
    df_saldo_banco_manual_db = pd.read_sql("SELECT * FROM saldo_banco_manual ORDER BY id DESC LIMIT 1", conn)

    if not df_banco_all.empty or not df_saldo_banco_manual_db.empty:
        if not df_banco_all.empty:
            df_banco_all["data"] = pd.to_datetime(df_banco_all["data"])
            df_banco_all["ano_mes"] = df_banco_all["data"].dt.strftime("%Y-%m")
            meses_banco = sorted(df_banco_all["ano_mes"].unique(), reverse=True)
        else:
            meses_banco = ["2026-08"]

        col_fb1, col_fb2 = st.columns([2, 4])
        with col_fb1:
            mes_banco_sel = st.selectbox("📅 Selecionar Mês do Extrato Bancário:", meses_banco)

        if not df_banco_all.empty:
            df_b = df_banco_all[df_banco_all["ano_mes"] == mes_banco_sel].copy()
            rec_b = df_b[df_b["tipo"] == "Receita"]["valor"].sum()
            desp_b = df_b[df_b["tipo"] == "Despesa"]["valor"].sum()
            saldo_b = rec_b - desp_b
        else:
            df_b = pd.DataFrame()
            rec_b = 0.0
            desp_b = 0.0
            saldo_b = 0.0

        saldo_real_total_banco = 0.0
        limite_utilizado_val = 0.0
        limite_disponivel_val = 0.0
        limite_total_val = 0.0

        if not df_saldo_banco_manual_db.empty:
            saldo_real_total_banco = float(df_saldo_banco_manual_db.iloc[0]["saldo_conta"])
            limite_utilizado_val = float(df_saldo_banco_manual_db.iloc[0]["limite_utilizado"])
            limite_disponivel_val = float(df_saldo_banco_manual_db.iloc[0]["limite_disponivel"])
            limite_total_val = float(df_saldo_banco_manual_db.iloc[0]["limite_total"])

        cb1, cb2, cb3, cb4 = st.columns(4)
        cb1.metric("🏦 Saldo no Banco", f"R$ {saldo_real_total_banco:,.2f}")
        cb2.metric("💰 Saldo Líquido do Mês", f"R$ {saldo_b:,.2f}")
        cb3.metric("🟢 Entradas", f"R$ {rec_b:,.2f}")
        cb4.metric("🔴 Saídas", f"R$ {desp_b:,.2f}")

        st.markdown("---")
        st.subheader("📋 Relação de Transações do Extrato PDF")
        if not df_b.empty:
            df_b["data"] = df_b["data"].dt.strftime("%d/%m/%Y")
            st.dataframe(df_b[["data", "tipo", "descricao", "categoria", "valor"]], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma transação encontrada para este mês.")
    else:
        st.info("Nenhum extrato bancário em PDF foi importado até o momento.")

else:
    botao_voltar()
    st.subheader(f"Página: {pagina}")
    st.info("Esta seção está integrada e ativa no seu banco de dados SQLite principal.")
