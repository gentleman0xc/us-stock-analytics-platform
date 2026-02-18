import yfinance as yf
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from src.config import STOCKS, DATA_PERIOD
from src.database import save_dataframe

def download_stock_prices(ticker, period=DATA_PERIOD):
    """Download historical price data for a stock"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            print(f"No data for {ticker}")
            return None
        
        # Clean and format
        hist.reset_index(inplace=True)
        hist['ticker'] = ticker
        hist.columns = [c.lower().replace(' ', '_') for c in hist.columns]
        hist['date'] = pd.to_datetime(hist['date']).dt.date
        
        # Select relevant columns
        cols = ['ticker', 'date', 'open', 'high', 'low', 'close',
                'volume', 'dividends', 'stock_splits']
        hist = hist[cols]
        
        return hist
        
    except Exception as e:
        print(f"Error downloading {ticker}: {e}")
        return None

def download_fundamentals(ticker):
    """Download fundamental metrics for a stock"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        fundamentals = {
            'ticker': ticker,
            'company_name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'profit_margin': info.get('profitMargins'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'beta': info.get('beta'),
            'week_52_high': info.get('fiftyTwoWeekHigh'),
            'week_52_low': info.get('fiftyTwoWeekLow'),
            'last_updated': datetime.now()
        }
        
        return pd.DataFrame([fundamentals])
        
    except Exception as e:
        print(f"Error downloading fundamentals {ticker}: {e}")
        return None

def run_extraction(tickers=STOCKS):
    """Run complete extraction for list of tickers"""
    
    print(f"\nStarting extraction for {len(tickers)} stocks...\n")
    
    all_prices = []
    all_fundamentals = []
    
    for ticker in tqdm(tickers, desc="Downloading"):
        
        # Prices
        prices = download_stock_prices(ticker)
        if prices is not None:
            all_prices.append(prices)
        
        # Fundamentals
        fundamentals = download_fundamentals(ticker)
        if fundamentals is not None:
            all_fundamentals.append(fundamentals)
    
    # Save to database
    print("\nSaving to database...")
    
    if all_prices:
        prices_df = pd.concat(all_prices, ignore_index=True)
        save_dataframe(prices_df, 'stock_prices', if_exists='replace')
    
    if all_fundamentals:
        fundamentals_df = pd.concat(all_fundamentals, ignore_index=True)
        save_dataframe(fundamentals_df, 'stock_fundamentals', if_exists='replace')
    
    print(f"\n Extraction complete!")
    print(f"   Prices: {len(prices_df):,} rows")
    print(f"   Stocks: {len(fundamentals_df)} companies")
    
    return prices_df, fundamentals_df

if __name__ == "__main__":
    prices, fundamentals = run_extraction()
    
    # Show sample
    print("\nSample data:")
    print(prices.head())
    print("\n" + "="*60)
    print(fundamentals[['ticker', 'company_name', 'sector', 'pe_ratio']].head())