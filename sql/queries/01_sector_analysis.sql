/* INSIGHTS DE NEGÓCIO:
   - Sharpe > 1.0: Setor excelente, retorno compensa o risco.
   - Correlação > 0.7: Setores "andando juntos", cuidado com a falta de diversificação.
   - P/E Ratio > 30: Setor possivelmente valorizado demais (caro).
*/

-- 1. Sector Performance Overview
-- Agrupa todas as ações por setor e identifica qual setor está "quente" ou "frio"
-- Métrica chave: avg_sharpe_ratio e avg_pe_ratio

SELECT 
    sf.sector,
    COUNT(DISTINCT sf.ticker) as num_stocks,
    ROUND(AVG(rm.annualized_return) * 100, 2) as avg_return_pct,
    ROUND(AVG(rm.sharpe_ratio), 2) as avg_sharpe_ratio,
    ROUND(AVG(rm.annualized_volatility) * 100, 2) as avg_volatility_pct,
    ROUND(AVG(sf.pe_ratio), 2) as avg_pe_ratio,
    ROUND(AVG(sf.market_cap) / 1e9, 1) as avg_market_cap_billions
FROM stock_fundamentals sf
JOIN risk_metrics rm ON sf.ticker = rm.ticker
WHERE sf.sector IS NOT NULL
  AND sf.sector != 'N/A'
GROUP BY sf.sector
ORDER BY avg_sharpe_ratio DESC;

-- 2. Best Stock per Sector (Highest Sharpe)
-- Ranqueamento para isolar apenas uma única ação por setor
-- Window Function para particionar os dados

WITH ranked_stocks AS (
    SELECT 
        sf.sector,
        sf.ticker,
        sf.company_name,
        rm.sharpe_ratio,
        rm.annualized_return,
        ROW_NUMBER() OVER (PARTITION BY sf.sector ORDER BY rm.sharpe_ratio DESC) as rank
    FROM stock_fundamentals sf
    JOIN risk_metrics rm ON sf.ticker = rm.ticker
    WHERE sf.sector IS NOT NULL
      AND sf.sector != 'N/A'
)
SELECT 
    sector,
    ticker,
    company_name,
    ROUND(sharpe_ratio, 2) as sharpe_ratio,
    ROUND(annualized_return * 100, 2) as return_pct
FROM ranked_stocks
WHERE rank = 1
ORDER BY sharpe_ratio DESC;

-- 3. Sector Correlation Matrix
-- compara o movimento diario de um setor contra todos os outros para diversificação

WITH daily_sector_returns AS (
    SELECT 
        DATE(sp.date) as trade_date,
        sf.sector,
        AVG(ti.daily_return) as sector_return
    FROM stock_prices sp
    JOIN technical_indicators ti ON sp.ticker = ti.ticker AND sp.date = ti.date
    JOIN stock_fundamentals sf ON sp.ticker = sf.ticker
    WHERE sf.sector IS NOT NULL
      AND sf.sector != 'N/A'
      AND sp.date >= CURRENT_DATE - INTERVAL '1 year'
    GROUP BY DATE(sp.date), sf.sector
)
SELECT 
    a.sector as sector_a,
    b.sector as sector_b,
    ROUND(CORR(a.sector_return, b.sector_return)::numeric, 3) as correlation
FROM daily_sector_returns a
JOIN daily_sector_returns b ON a.trade_date = b.trade_date
WHERE a.sector < b.sector  -- Avoid duplicates
GROUP BY a.sector, b.sector
HAVING COUNT(*) > 200  -- Minimum data points
ORDER BY ABS(CORR(a.sector_return, b.sector_return)) DESC
LIMIT 20;