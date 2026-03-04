/* INSIGHTS DE OTIMIZAÇÃO E ALOCAÇÃO:
   - Alocação Baseada em Sharpe -> Atribui mais peso às ações que entregam retorno 
     com menos volatilidade

   - Status de Diversificação -> Evita que um único setor domine mais de 
     30% da carteira, protegendo contra crises específicas de um setor

   - Simulação de Performance -> Mostra o "passado" da sua carteira teórica para 
     validar se a estratégia de escolher os Top 10 realmente teria funcionado
*/

-- 1. Suggested Portfolio Allocation (Sharpe-based)
WITH top_performers AS (
    SELECT 
        rm.ticker,
        sf.company_name,
        sf.sector,
        rm.sharpe_ratio,
        rm.annualized_return,
        rm.annualized_volatility
    FROM risk_metrics rm
    JOIN stock_fundamentals sf ON rm.ticker = sf.ticker
    WHERE rm.sharpe_ratio > 0.5  
    ORDER BY rm.sharpe_ratio DESC
    LIMIT 15  -- Top 15 
)
SELECT 
    ticker,
    company_name,
    sector,
    ROUND(sharpe_ratio, 2) as sharpe_ratio,
    ROUND(annualized_return * 100, 2) as expected_return_pct,
    ROUND(annualized_volatility * 100, 2) as volatility_pct,
    -- sugestões baseado em Sharpe ratio
    ROUND((sharpe_ratio / SUM(sharpe_ratio) OVER ()) * 100, 1) as suggested_allocation_pct
FROM top_performers
ORDER BY sharpe_ratio DESC;


-- 2. Sector Diversification Check
-- agrupa suas sugestões de investimento por setor e verifica se você não está concentrado demais em uma única área
WITH portfolio AS (
    SELECT 
        sf.sector,
        COUNT(*) as num_stocks,
        SUM(rm.sharpe_ratio) as total_sharpe
    FROM risk_metrics rm
    JOIN stock_fundamentals sf ON rm.ticker = sf.ticker
    WHERE rm.sharpe_ratio > 0.5
    GROUP BY sf.sector
)
SELECT 
    sector,
    num_stocks,
    ROUND(total_sharpe, 2) as sector_sharpe,
    ROUND((total_sharpe / SUM(total_sharpe) OVER ()) * 100, 1) as sector_allocation_pct,
    CASE 
        WHEN (total_sharpe / SUM(total_sharpe) OVER ()) > 0.30 THEN 'OVERWEIGHT'
        WHEN (total_sharpe / SUM(total_sharpe) OVER ()) < 0.10 THEN 'UNDERWEIGHT'
        ELSE 'BALANCED'
    END as diversification_status
FROM portfolio
ORDER BY sector_allocation_pct DESC;


-- 3. Simulated Portfolio Performance
-- simula como seria o rendimento se você tivesse investido nas 10 melhores ações (Top 10 por Sharpe) no passado
WITH top_10 AS (
    SELECT ticker
    FROM risk_metrics
    ORDER BY sharpe_ratio DESC
    LIMIT 10
),
portfolio_returns AS (
    SELECT 
        ti.date,
        AVG(ti.daily_return) as portfolio_return
    FROM technical_indicators ti
    WHERE ti.ticker IN (SELECT ticker FROM top_10)
      AND ti.daily_return IS NOT NULL
    GROUP BY ti.date
)
SELECT 
    COUNT(*) as trading_days,
    ROUND((AVG(portfolio_return) * 252 * 100)::numeric, 2) as annualized_return_pct,
    ROUND((STDDEV(portfolio_return) * SQRT(252) * 100)::numeric, 2) as annualized_volatility_pct,
    ROUND(((AVG(portfolio_return) * 252 - 0.045) / (STDDEV(portfolio_return) * SQRT(252)))::numeric, 2) as sharpe_ratio,
    ROUND((MIN(portfolio_return) * 100)::numeric, 2) as worst_day_pct,
    ROUND((MAX(portfolio_return) * 100)::numeric, 2) as best_day_pct
FROM portfolio_returns;