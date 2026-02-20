import pandas as pd
import numpy as np
from src.database import query_to_df, save_dataframe
from src.config import RISK_FREE_RATE

def calculate_all_indicators(df):
    """Calculate all technical indicators for all stocks"""
    print("Calculating technical indicators...")
    
    df = df.sort_values(['ticker', 'date']).copy()
    results = []
    
    for ticker in df['ticker'].unique():
        stock_df = df[df['ticker'] == ticker].copy()
        stock_df = _add_indicators(stock_df)
        results.append(stock_df)
        print(f"   ✅ {ticker}")
    
    return pd.concat(results, ignore_index=True)


def _add_indicators(df):
    """Add all technical indicators for a single stock"""
    
    close = df['close'].astype(float)
    
    # 1. Simple Moving Averages
    df['sma_20'] = close.rolling(window=20).mean()
    df['sma_50'] = close.rolling(window=50).mean()
    df['sma_200'] = close.rolling(window=200).mean()
    
    # 2. RSI (Relative Strength Index)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # 3. MACD (Moving Average Convergence Divergence)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # 4. Bollinger Bands
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    df['bb_upper'] = sma_20 + (std_20 * 2)
    df['bb_middle'] = sma_20
    df['bb_lower'] = sma_20 - (std_20 * 2)
    
    # 5. Returns and Volatility
    df['daily_return'] = close.pct_change()
    df['volatility_30d'] = df['daily_return'].rolling(window=30).std() * np.sqrt(252)
    
    return df


def calculate_risk_metrics(df):
    """Calculate risk metrics per ticker"""
    
    print("\n Calculating risk metrics...")
    results = []
    
    for ticker in df['ticker'].unique():
        stock_returns = df[df['ticker'] == ticker]['daily_return'].dropna()
        
        if len(stock_returns) < 30:
            print(f"   ⚠️  {ticker}: Not enough data")
            continue
        
        # Annual returns
        ann_return = stock_returns.mean() * 252
        ann_volatility = stock_returns.std() * np.sqrt(252)
        
        # Sharpe Ratio
        excess_return = ann_return - RISK_FREE_RATE
        sharpe = excess_return / ann_volatility if ann_volatility > 0 else 0
        
        # Maximum Drawdown
        cum_returns = (1 + stock_returns).cumprod()
        rolling_max = cum_returns.expanding().max()
        drawdown = (cum_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Value at Risk (95% confidence)
        var_95 = stock_returns.quantile(0.05)
        
        # Sortino Ratio (downside volatility only)
        downside_returns = stock_returns[stock_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino = excess_return / downside_std if downside_std > 0 else 0
        
        results.append({
            'ticker': ticker,
            'sharpe_ratio': round(sharpe, 4),
            'sortino_ratio': round(sortino, 4),
            'max_drawdown': round(max_drawdown, 6),
            'var_95': round(var_95, 6),
            'annualized_return': round(ann_return, 6),
            'annualized_volatility': round(ann_volatility, 6),
        })
        
        print(f"   ✅ {ticker}: Sharpe={sharpe:.2f}")
    
    return pd.DataFrame(results)


def run_indicators_pipeline():
    """Execute complete indicators pipeline"""
    
    print("\n" + "="*60)
    print("TECHNICAL INDICATORS PIPELINE")
    print("="*60 + "\n")
    
    # Load price data
    print("Loading price data from database...")
    prices_df = query_to_df("SELECT * FROM stock_prices ORDER BY ticker, date")
    
    if prices_df is None or len(prices_df) == 0:
        print("No price data found. Run data_extractor.py first!")
        return None, None
    
    print(f"Loaded {len(prices_df):,} rows")
    
    # Calculate technical indicators
    print()
    indicators_df = calculate_all_indicators(prices_df)
    
    # Select columns to save
    cols = ['ticker', 'date', 'sma_20', 'sma_50', 'sma_200',
            'rsi_14', 'macd', 'macd_signal', 'bb_upper',
            'bb_middle', 'bb_lower', 'daily_return', 'volatility_30d']
    
    # Save to database
    print("\nSaving technical indicators to database...")
    save_dataframe(indicators_df[cols], 'technical_indicators', if_exists='replace')
    
    # Calculate risk metrics
    risk_df = calculate_risk_metrics(indicators_df)
    
    # Save risk metrics
    print("\nSaving risk metrics to database...")
    save_dataframe(risk_df, 'risk_metrics', if_exists='replace')
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Technical Indicators: {len(indicators_df):,} rows saved")
    print(f"Risk Metrics: {len(risk_df)} stocks calculated")
    print(f"\nTop 5 by Sharpe Ratio:")
    print(risk_df.nlargest(5, 'sharpe_ratio')[['ticker', 'sharpe_ratio', 'annualized_return']])
    print("="*60 + "\n")
    
    return indicators_df, risk_df


if __name__ == "__main__":
    indicators_df, risk_df = run_indicators_pipeline()