# cogs/stocks_core.py
import database as sqlite3
from cogs.eco_stocks_list import TOP_200_STOCKS

def get_db():
    return sqlite3.connect("warnings.db")

def get_stock_cap(ticker):
    if ticker.startswith("STK"):
        try:
            stk_num = int(ticker[3:])
            if stk_num <= 50:
                return 500
            elif stk_num <= 100:
                return 2500
            else:
                return 10000
        except ValueError:
            return 10000
    elif ticker in ["NIFTY", "SENSEX", "BTC", "MARUTI", "ULTRAC"]:
        return 300000
    else:
        return 50000

def init_stocks_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Master Stocks Table Setup
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        ticker TEXT PRIMARY KEY,
        company_name TEXT,
        current_price INTEGER,
        last_change TEXT DEFAULT '0%',
        available_shares INTEGER DEFAULT 10000
    )
    """)
    
    # User Portfolios Table: Added profile_privacy column (Default = public)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolios (
        user_id TEXT,
        ticker TEXT,
        shares INTEGER DEFAULT 0,
        profile_privacy TEXT DEFAULT 'public',
        avg_buy_price REAL DEFAULT 0,
        PRIMARY KEY (user_id, ticker)
    )
    """)
    
    # Add avg_buy_price if missing
    try:
        cursor.execute("ALTER TABLE portfolios ADD COLUMN avg_buy_price REAL DEFAULT 0")
    except Exception:
        pass
    
    # Core Database initialization sync loop
    for ticker, name, price in TOP_200_STOCKS:
        cursor.execute("""
        INSERT OR IGNORE INTO stocks (ticker, company_name, current_price, available_shares) 
        VALUES (?, ?, ?, 10000)
        """, (ticker, name, price))
        
        # Apply cap to correct overly inflated DB prices automatically
        cap = get_stock_cap(ticker)
        cursor.execute("UPDATE stocks SET current_price = ? WHERE ticker = ? AND current_price > ?", (cap, ticker, cap))
        
    conn.commit()
    conn.close()

# Structural Volatility configurations for multi-file cross reads
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}