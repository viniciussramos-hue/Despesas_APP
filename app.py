with aba2:
    st.subheader("📊 Dashboard e Projeções")
    df = carregar_dados()
    if not df.empty:
        # Cálculos de Totais
        df['valor'] = pd.to_numeric(df['valor'])
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        
        # Projeção de Gastos
        dia_hoje = datetime.now().day
        dias_no_mes = 30
        media_diaria = despesas / max(dia_hoje, 1)
        projecao_final = media_diaria * dias_no_mes
        
        # Colunas de métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Saldo Atual", f"R$ {receitas - despesas:.2f}")
        col2.metric("Total Despesas", f"R$ {despesas:.2f}")
        col3.metric("Projeção Fim do Mês", f"R$ {projecao_final:.2f}", delta=f"R$ {orcamento_mes - projecao_final:.2f}", delta_color="inverse")

        # Alerta visual da projeção
        if projecao_final > orcamento_mes:
            st.error(f"⚠️ Atenção: Sua projeção de R$ {projecao_final:.2f} está acima do seu orçamento de R$ {orcamento_mes:.2f}!")
        else:
            st.success(f"✅ Parabéns: Sua projeção de R$ {projecao_final:.2f} está dentro do seu orçamento!")

        st.markdown("---")
        
        # Filtro de Período e Gráfico
        st.write("### Gastos por Categoria")
        df['data'] = pd.to_datetime(df['data'])
        st.bar_chart(df[df['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum())
    else:
        st.info("Lançe suas primeiras despesas para ver a projeção.")
