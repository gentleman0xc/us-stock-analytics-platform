import pandas as pd
from datetime import datetime
from src.database import query_to_df, save_dataframe

def generate_signals_for_ticker(ticker, indicators_df):
    """Generate trading signals for a single ticker"""
    
    stock = indicators_df[indicators_df['ticker'] == ticker].sort_values('date')
    
    if len(stock) < 2:
        return []
    
    latest = stock.iloc[-1]
    previous = stock.iloc[-2]
    signal_date = latest['date']
    signals = []
    
    # Signal 1: Golden Cross (bullish long-term)
    if (latest['sma_50'] > latest['sma_200'] and 
        previous['sma_50'] <= previous['sma_200']):
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'GOLDEN_CROSS',
            'signal_strength': 'STRONG',
            'description': 'SMA50 crossed above SMA200 - Strong bullish long-term signal'
        })
    
    # Signal 2: Death Cross (bearish long-term)
    if (latest['sma_50'] < latest['sma_200'] and 
        previous['sma_50'] >= previous['sma_200']):
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'DEATH_CROSS',
            'signal_strength': 'STRONG',
            'description': 'SMA50 crossed below SMA200 - Strong bearish long-term signal'
        })
    
    # Signal 3: RSI Oversold (potential buy)
    rsi = latest['rsi_14']
    if pd.notna(rsi) and rsi < 30:
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'RSI_OVERSOLD',
            'signal_strength': 'MEDIUM',
            'description': f'RSI at {rsi:.1f} - Stock potentially oversold, consider buying'
        })
    
    # Signal 4: RSI Overbought (potential sell)
    if pd.notna(rsi) and rsi > 70:
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'RSI_OVERBOUGHT',
            'signal_strength': 'MEDIUM',
            'description': f'RSI at {rsi:.1f} - Stock potentially overbought, consider selling'
        })
    
    # Signal 5: MACD Bullish Crossover
    if (pd.notna(latest['macd']) and pd.notna(latest['macd_signal']) and
        latest['macd'] > latest['macd_signal'] and 
        previous['macd'] <= previous['macd_signal']):
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'MACD_BULLISH',
            'signal_strength': 'MEDIUM',
            'description': 'MACD crossed above signal line - Bullish momentum building'
        })
    
    # Signal 6: MACD Bearish Crossover
    if (pd.notna(latest['macd']) and pd.notna(latest['macd_signal']) and
        latest['macd'] < latest['macd_signal'] and 
        previous['macd'] >= previous['macd_signal']):
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'MACD_BEARISH',
            'signal_strength': 'MEDIUM',
            'description': 'MACD crossed below signal line - Bearish momentum building'
        })
    
    # Signal 7: Bollinger Bands Oversold
    close = latest['close']
    if pd.notna(latest['bb_lower']) and close < latest['bb_lower']:
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'BB_OVERSOLD',
            'signal_strength': 'WEAK',
            'description': f'Price ({close:.2f}) below lower Bollinger Band - Potential bounce'
        })
    
    # Signal 8: Bollinger Bands Overbought
    if pd.notna(latest['bb_upper']) and close > latest['bb_upper']:
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'BB_OVERBOUGHT',
            'signal_strength': 'WEAK',
            'description': f'Price ({close:.2f}) above upper Bollinger Band - Potential pullback'
        })
    
    # If no signals, mark as NEUTRAL
    if not signals:
        signals.append({
            'ticker': ticker,
            'signal_date': signal_date,
            'signal_type': 'NEUTRAL',
            'signal_strength': 'NEUTRAL',
            'description': 'No significant technical signals detected'
        })
    
    return signals


def run_signals_pipeline():
    """Generate signals for all tickers"""
    
    print("\n" + "="*60)
    print("TRADING SIGNALS GENERATION")
    print("="*60 + "\n")
    
    # Load indicators
    print("Loading technical indicators from database...")
    indicators_df = query_to_df("""
        SELECT ti.*, sp.close 
        FROM technical_indicators ti
        JOIN stock_prices sp ON ti.ticker = sp.ticker AND ti.date = sp.date
        ORDER BY ti.ticker, ti.date
    """)
    
    if indicators_df is None or len(indicators_df) == 0:
        print("No indicators found. Run technical_indicators.py first!")
        return None
    
    print(f"   ✅ Loaded {len(indicators_df):,} rows\n")
    
    # Generate signals for each ticker
    print("Generating trading signals...")
    all_signals = []
    
    for ticker in indicators_df['ticker'].unique():
        signals = generate_signals_for_ticker(ticker, indicators_df)
        all_signals.extend(signals)
        
        # Show summary for this ticker
        signal_types = [s['signal_type'] for s in signals]
        if 'NEUTRAL' not in signal_types:
            print(f"   📊 {ticker}: {', '.join(signal_types)}")
    
    # Convert to DataFrame
    signals_df = pd.DataFrame(all_signals)
    
    # Save to database
    print("\nSaving signals to database...")
    save_dataframe(signals_df, 'trading_signals', if_exists='replace')
    
    # Summary statistics
    print("\n" + "="*60)
    print("SIGNAL SUMMARY")
    print("="*60)
    print(f"Total signals generated: {len(signals_df)}")
    print(f"\nSignals by Type:")
    signal_counts = signals_df['signal_type'].value_counts()
    for signal_type, count in signal_counts.items():
        print(f"   {signal_type}: {count}")
    
    print(f"\nSignals by Strength:")
    strength_counts = signals_df['signal_strength'].value_counts()
    for strength, count in strength_counts.items():
        print(f"   {strength}: {count}")
    
    # Show BUY opportunities
    buy_signals = signals_df[signals_df['signal_type'].isin([
        'GOLDEN_CROSS', 'RSI_OVERSOLD', 'MACD_BULLISH', 'BB_OVERSOLD'
    ])]
    
    if len(buy_signals) > 0:
        print(f"\nBUY Opportunities ({len(buy_signals)}):")
        for _, signal in buy_signals.iterrows():
            print(f"   {signal['ticker']}: {signal['signal_type']} ({signal['signal_strength']})")
    
    # Show SELL opportunities
    sell_signals = signals_df[signals_df['signal_type'].isin([
        'DEATH_CROSS', 'RSI_OVERBOUGHT', 'MACD_BEARISH', 'BB_OVERBOUGHT'
    ])]
    
    if len(sell_signals) > 0:
        print(f"\nSELL Opportunities ({len(sell_signals)}):")
        for _, signal in sell_signals.iterrows():
            print(f"   {signal['ticker']}: {signal['signal_type']} ({signal['signal_strength']})")
    
    print("="*60 + "\n")
    
    return signals_df


if __name__ == "__main__":
    signals_df = run_signals_pipeline()