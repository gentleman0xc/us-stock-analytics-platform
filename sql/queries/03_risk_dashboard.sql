/* INSIGHTS DE NEGÓCIO - GESTÃO DE RISCO:
   - Volatilidade < 20%: Ativos de perfil conservador 

   - VaR 95% (Value at Risk): Diz que em 95% dos dias, sua perda máxima não deve 
     ultrapassar este valor
*/

-- 1. Risk Profile by Stock
-- ranking de todas as  ações, classificando-as em níveis de risco (low, medium, high)
SELECT 
    rm.ticker,
    sf.company_name,
    sf.sector,
    ROUND(sf.market_cap / 1e9, 1) as market_cap_billions,
    ROUND(rm.annualized_return * 100, 2) as return_pct,
    ROUND(rm.annualized_volatility * 100, 2) as volatility_pct,
    ROUND(rm.sharpe_ratio, 2) as sharpe_ratio,
    ROUND(rm.max_drawdown * 100, 2) as max_drawdown_pct,
    ROUND(rm.var_95 * 100, 2) as var_95_pct,
    CASE 
        WHEN rm.annualized_volatility < 0.20 THEN 'LOW'
        WHEN rm.annualized_volatility < 0.35 THEN 'MEDIUM'
        ELSE 'HIGH'
    END as risk_level
FROM risk_metrics rm
JOIN stock_fundamentals sf ON rm.ticker = sf.ticker
ORDER BY sf.market_cap DESC;


-- 2. Efficient Frontier (Risk vs Return)
-- separa as ações em quatro quadrantes
SELECT 
    ticker,
    ROUND(annualized_return * 100, 2) as return_pct,
    ROUND(annualized_volatility * 100, 2) as volatility_pct,
    ROUND(sharpe_ratio, 2) as sharpe_ratio,
    -- Quadrant
    CASE 
        WHEN annualized_return > 0.10 AND annualized_volatility < 0.25 THEN 'HIGH_RETURN_LOW_RISK'
        WHEN annualized_return > 0.10 AND annualized_volatility >= 0.25 THEN 'HIGH_RETURN_HIGH_RISK'
        WHEN annualized_return <= 0.10 AND annualized_volatility < 0.25 THEN 'LOW_RETURN_LOW_RISK'
        ELSE 'LOW_RETURN_HIGH_RISK'
    END as risk_return_quadrant
FROM risk_metrics
ORDER BY sharpe_ratio DESC;


-- 3. Portfolio Diversification Candidates
-- cruzar todas as ações entre si para encontrar pares que tenham uma baixa correlação 
WITH stock_returns AS (
    SELECT 
        ticker,
        date,
        daily_return
    FROM technical_indicators
    WHERE date >= CURRENT_DATE - INTERVAL '1 year'
      AND daily_return IS NOT NULL
)
SELECT 
    a.ticker as stock_a,
    b.ticker as stock_b,
    ROUND(CORR(a.daily_return, b.daily_return)::numeric, 3) as correlation
FROM stock_returns a
JOIN stock_returns b ON a.date = b.date
WHERE a.ticker < b.ticker
GROUP BY a.ticker, b.ticker
HAVING COUNT(*) > 200
  AND ABS(CORR(a.daily_return, b.daily_return)) < 0.3  -- baixa correlação
ORDER BY ABS(CORR(a.daily_return, b.daily_return));