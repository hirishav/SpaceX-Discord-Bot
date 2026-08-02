# cogs/stocks_core.py
import sqlite3
from cogs.eco_stocks_list import TOP_200_STOCKS

def get_db():
    return sqlite3.connect("warnings.db")

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
        PRIMARY KEY (user_id, ticker)
    )
    """)
    
    # Core Database initialization sync loop
    for ticker, name, price in TOP_200_STOCKS:
        cursor.execute("""
        INSERT OR IGNORE INTO stocks (ticker, company_name, current_price, available_shares) 
        VALUES (?, ?, ?, 10000)
        """, (ticker, name, price))
        
    conn.commit()
    conn.close()

# Structural Volatility configurations for multi-file cross reads
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}