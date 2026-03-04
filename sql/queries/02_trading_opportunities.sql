/* INSIGHTS DE NEGÓCIO - ESTRATÉGIA DE TRADING:
   - Sinais de CONFLUÊNCIA (Multi-Signal): Ações com 2 ou mais sinais técnicos têm 
     maior probabilidade de acerto (confirmação de tendência)

   - Filtro Fundamentalista: Evite comprar apenas pelo gráfico. O P/E Ratio < 30 
     garante que você não está entrando em uma "bolha"

   - Sharpe > 0.5: Filtra ativos que possuem um histórico de retorno consistente 
     frente ao risco

   - RSI < 30: Indica que o ativo está barato (sobrevendido) no curto prazo
*/


-- 1. Current Buy Signals (Strong + Medium)
-- Nosso scanner de oportunidades semanal, focando apenas nos ultimos 7 dias
SELECT 
    ts.ticker,
    sf.company_name,
    sf.sector,
    ts.signal_type,
    ts.signal_strength,
    ts.description,
    ROUND(rm.sharpe_ratio, 2) as sharpe_ratio,
    ROUND(sf.pe_ratio, 2) as pe_ratio,
    ts.signal_date
FROM trading_signals ts
JOIN stock_fundamentals sf ON ts.ticker = sf.ticker
JOIN risk_metrics rm ON ts.ticker = rm.ticker
WHERE ts.signal_type IN ('GOLDEN_CROSS', 'RSI_OVERSOLD', 'MACD_BULLISH', 'BB_OVERSOLD')
  AND ts.signal_strength IN ('STRONG', 'MEDIUM')
  AND ts.signal_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY 
    CASE ts.signal_strength 
        WHEN 'STRONG' THEN 1 
        WHEN 'MEDIUM' THEN 2 
    END,
    rm.sharpe_ratio DESC;

-- 2. Multi-Signal Stocks (High Conviction)
-- Identifica ativos que dispararam múltiplos sinais diferentes
SELECT 
    ticker,
    COUNT(*) as num_signals,
    STRING_AGG(signal_type, ', ' ORDER BY signal_type) as signals,
    MAX(signal_date) as latest_signal_date
FROM trading_signals
WHERE signal_type != 'NEUTRAL'
  AND signal_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ticker
HAVING COUNT(*) >= 2  -- At least 2 different signals
ORDER BY num_signals DESC, ticker;


-- 3. Signals with Fundamental Screening
-- nosso filtro de qualidade
SELECT 
    ts.ticker,
    sf.company_name,
    sf.sector,
    ts.signal_type,
    ROUND(sf.pe_ratio::numeric, 2) as pe_ratio,
    ROUND(rm.sharpe_ratio::numeric, 2) as sharpe_ratio,
    ROUND((sf.dividend_yield * 100)::numeric, 2) as div_yield_pct,
    ROUND((rm.annualized_return * 100)::numeric, 2) as ann_return_pct
FROM trading_signals ts
JOIN stock_fundamentals sf ON ts.ticker = sf.ticker
JOIN risk_metrics rm ON ts.ticker = rm.ticker
WHERE ts.signal_type IN ('GOLDEN_CROSS', 'RSI_OVERSOLD', 'MACD_BULLISH')
  AND sf.pe_ratio < 30  -- não estar cara demais
  AND sf.pe_ratio > 0   -- a empresa precisa ser lucrativa
  AND rm.sharpe_ratio > 0.5  -- ter bons retornos ajustados ao risco
  AND ts.signal_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY rm.sharpe_ratio DESC;