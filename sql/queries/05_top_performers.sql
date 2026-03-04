/* INSIGHTS DO RANKING FINAL
   - Composite Score: ranking equilibrado entre retorno, risco (Sharpe) e dividendos
   - Momentum: ações que subiram nos últimos 12 meses tendem a manter a alta no curto prazo
   - Dividend Aristocrats: empresas sólidas, lucrativas e com P/L < 25 que pagam dividendos
*/


-- 1. Top Performers by Multiple Metrics

SELECT 
    rm.ticker,
    sf.company_name,
    sf.sector,
    ROUND(rm.annualized_return * 100, 2) as return_pct,
    ROUND(rm.sharpe_ratio, 2) as sharpe_ratio,
    ROUND(sf.pe_ratio, 2) as pe_ratio,
    ROUND(sf.dividend_yield * 100, 2) as div_yield_pct,
    ROUND(sf.market_cap / 1e9, 1) as market_cap_billions,
    -- Score 
    ROUND(
        (rm.sharpe_ratio * 0.4 + 
         (rm.annualized_return * 100) * 0.3 + 
         (COALESCE(sf.dividend_yield, 0) * 100) * 0.3), 
        2
    ) as composite_score
FROM risk_metrics rm
JOIN stock_fundamentals sf ON rm.ticker = sf.ticker
WHERE rm.sharpe_ratio > 0
ORDER BY composite_score DESC
LIMIT 20;


-- 2. Momentum Strategy (12-month winners)
WITH price_changes AS (
    SELECT 
        ticker,
        MAX(CASE WHEN date = (SELECT MAX(date) FROM stock_prices) 
            THEN close END) as current_price,
        MAX(CASE WHEN date = (SELECT MAX(date) - INTERVAL '12 months' 
            FROM stock_prices) THEN close END) as price_12m_ago
    FROM stock_prices
    GROUP BY ticker
)
SELECT 
    pc.ticker,
    sf.company_name,
    sf.sector,
    ROUND(pc.current_price, 2) as current_price,
    ROUND(((pc.current_price - pc.price_12m_ago) / pc.price_12m_ago * 100), 2) as return_12m_pct,
    ROUND(rm.sharpe_ratio, 2) as sharpe_ratio,
    ROUND(rm.max_drawdown * 100, 2) as max_drawdown_pct
FROM price_changes pc
JOIN stock_fundamentals sf ON pc.ticker = sf.ticker
JOIN risk_metrics rm ON pc.ticker = rm.ticker
WHERE pc.price_12m_ago IS NOT NULL
  AND pc.current_price IS NOT NULL
ORDER BY return_12m_pct DESC
LIMIT 20;


-- 3. Dividend Aristocrats (High Yield + Growth)
SELECT 
    sf.ticker,
    sf.company_name,
    sf.sector,
    ROUND((sf.dividend_yield * 100)::numeric, 2) as div_yield_pct,
    ROUND((sf.revenue_growth * 100)::numeric, 2) as revenue_growth_pct,
    ROUND((sf.earnings_growth * 100)::numeric, 2) as earnings_growth_pct,
    ROUND(sf.pe_ratio::numeric, 2) as pe_ratio,
    ROUND(rm.sharpe_ratio::numeric, 2) as sharpe_ratio,
    ROUND((rm.annualized_return * 100)::numeric, 2) as return_pct
FROM stock_fundamentals sf
JOIN risk_metrics rm ON sf.ticker = rm.ticker
WHERE sf.dividend_yield > 0.02  -- Rendimento > 2%
  AND sf.revenue_growth > 0 -- crescimento positivo
  AND sf.pe_ratio < 25 -- Preço justo (não sobrevalorizada)
  AND sf.pe_ratio > 0 -- Empresa lucrativa
ORDER BY sf.dividend_yield DESC
LIMIT 15;