<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestor Financeiro Profissional</title>
    <style>
        :root {
            --bg-color: #0f1117;
            --card-bg: rgba(25, 29, 38, 0.75);
            --card-hover: rgba(35, 41, 54, 0.9);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.2);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
            --accent-gold: #f59e0b;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            padding: 40px 20px;
            min-height: 100vh;
            background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.08) 0%, transparent 60%);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            margin-bottom: 30px;
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            color: #ffffff;
        }

        .header-title span {
            font-size: 32px;
        }

        .header-subtitle {
            color: var(--text-secondary);
            font-size: 15px;
        }

        /* Section Indicator */
        .section-indicator {
            margin-top: 25px;
            margin-bottom: 20px;
        }

        .section-indicator h2 {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }

        .section-indicator p {
            color: var(--text-secondary);
            font-size: 13px;
        }

        /* Groups Layout */
        .dashboard-groups {
            display: flex;
            flex-direction: column;
            gap: 28px;
        }

        .group-card {
            background: rgba(18, 21, 28, 0.5);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }

        .group-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .grid-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
        }

        /* Action Buttons / Cards */
        .nav-btn {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 14px 18px;
            color: var(--text-primary);
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: all 0.25s ease;
            text-decoration: none;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .nav-btn:hover {
            background: var(--card-hover);
            border-color: var(--border-hover);
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
        }

        .nav-btn-content {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .icon-box {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            background: rgba(255, 255, 255, 0.05);
        }

        /* Cores customizadas para os ícones */
        .btn-red .icon-box { color: var(--accent-red); background: rgba(239, 68, 68, 0.1); }
        .btn-green .icon-box { color: var(--accent-green); background: rgba(34, 197, 94, 0.1); }
        .btn-gold .icon-box { color: var(--accent-gold); background: rgba(245, 158, 11, 0.1); }
        .btn-blue .icon-box { color: var(--accent-blue); background: rgba(59, 130, 246, 0.1); }
        .btn-purple .icon-box { color: var(--accent-purple); background: rgba(139, 92, 246, 0.1); }

        .arrow-indicator {
            color: var(--text-secondary);
            font-size: 12px;
            opacity: 0.5;
            transition: opacity 0.2s, transform 0.2s;
        }

        .nav-btn:hover .arrow-indicator {
            opacity: 1;
            transform: translateX(3px);
        }

        @media (max-width: 768px) {
            .grid-buttons {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-title">
                <span>💸</span> Gestor Financeiro Profissional
            </div>
            <div class="header-subtitle">
                Sistema avançado de controle orçamentário, investimentos, projeções e auditoria de holerites.
            </div>

            <div class="section-indicator">
                <h2><span>🎛️</span> Painel de Indicadores & Acesso Rápido</h2>
                <p>Clique em um dos botões abaixo para acessar a respectiva seção do sistema:</p>
            </div>
        </div>

        <!-- Grupos de Acesso -->
        <div class="dashboard-groups">
            
            <!-- Grupo 1: Painel de Gestão Diária -->
            <div class="group-card">
                <div class="group-title">Painel de Gestão Diária</div>
                <div class="grid-buttons">
                    <a href="#lancar-despesa" class="nav-btn btn-red">
                        <div class="nav-btn-content">
                            <div class="icon-box">🔴</div>
                            <span>Lançar Despesa</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#entradas" class="nav-btn btn-green">
                        <div class="nav-btn-content">
                            <div class="icon-box">🟢</div>
                            <span>Entradas & Salários</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#contas-pagar" class="nav-btn btn-gold">
                        <div class="nav-btn-content">
                            <div class="icon-box">📅</div>
                            <span>Contas a Pagar</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#cartao" class="nav-btn btn-gold">
                        <div class="nav-btn-content">
                            <div class="icon-box">💳</div>
                            <span>Cartão de Crédito</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#fluxo" class="nav-btn btn-green">
                        <div class="nav-btn-content">
                            <div class="icon-box">📊</div>
                            <span>Fluxo de Caixa</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>
                </div>
            </div>

            <!-- Grupo 2: Análise & Planejamento -->
            <div class="group-card">
                <div class="group-title">Análise & Planejamento</div>
                <div class="grid-buttons">
                    <a href="#investimentos" class="nav-btn btn-blue">
                        <div class="nav-btn-content">
                            <div class="icon-box">📈</div>
                            <span>Investimentos</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#projecoes" class="nav-btn btn-purple">
                        <div class="nav-btn-content">
                            <div class="icon-box">🔮</div>
                            <span>Projeções Futuras</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#dashboard" class="nav-btn btn-blue">
                        <div class="nav-btn-content">
                            <div class="icon-box">📊</div>
                            <span>Dashboard Geral</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#desafios" class="nav-btn btn-gold">
                        <div class="nav-btn-content">
                            <div class="icon-box">🎯</div>
                            <span>Desafios</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#metas" class="nav-btn btn-gold">
                        <div class="nav-btn-content">
                            <div class="icon-box">🎯</div>
                            <span>Metas de Gastos</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>
                </div>
            </div>

            <!-- Grupo 3: Configuração & Suporte -->
            <div class="group-card">
                <div class="group-title">Configuração & Suporte</div>
                <div class="grid-buttons">
                    <a href="#categorias" class="nav-btn btn-gold">
                        <div class="nav-btn-content">
                            <div class="icon-box">🏷️</div>
                            <span>Categorias & Ícones</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#saude" class="nav-btn btn-red">
                        <div class="nav-btn-content">
                            <div class="icon-box">❤️</div>
                            <span>Saúde Financeira</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>
                </div>
            </div>

            <!-- Grupo 4: Relatórios & Backup -->
            <div class="group-card">
                <div class="group-title">Relatórios & Backup</div>
                <div class="grid-buttons">
                    <a href="#holerites" class="nav-btn btn-blue">
                        <div class="nav-btn-content">
                            <div class="icon-box">📄</div>
                            <span>Holerites & PDF</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>

                    <a href="#extrato" class="nav-btn btn-blue">
                        <div class="nav-btn-content">
                            <div class="icon-box">📋</div>
                            <span>Extrato & Backup</span>
                        </div>
                        <span class="arrow-indicator">➔</span>
                    </a>
                </div>
            </div>

        </div>
    </div>

</body>
</html>
