# database.py - Universal Database Engine (PostgreSQL / SQLite Seamless Bridge)
import os
import re
import sqlite3 as _sqlite3
import logging

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# Re-export sqlite3 exceptions and attributes for compatibility
Error = _sqlite3.Error
OperationalError = _sqlite3.OperationalError
IntegrityError = _sqlite3.IntegrityError
DatabaseError = _sqlite3.DatabaseError

def get_database_url():
    try:
        import config
        url = getattr(config, 'DATABASE_URL', os.getenv('DATABASE_URL'))
    except (ImportError, AttributeError):
        url = os.getenv('DATABASE_URL')
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

class PostgresCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def _translate_query(self, query):
        q_strip = query.strip()
        # Ignore SQLite Pragmas
        if q_strip.upper().startswith("PRAGMA"):
            return None

        # Table Creation Translations
        if "CREATE TABLE" in query.upper():
            query = re.sub(r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b', 'SERIAL PRIMARY KEY', query, flags=re.IGNORECASE)
            query = re.sub(r'\bAUTOINCREMENT\b', '', query, flags=re.IGNORECASE)
            query = re.sub(r'\bDATETIME\s+DEFAULT\s+CURRENT_TIMESTAMP\b', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP', query, flags=re.IGNORECASE)

        # INSERT OR IGNORE / INSERT OR REPLACE Translations
        q_upper = query.upper()
        if "INSERT OR IGNORE" in q_upper:
            query = re.sub(r'\bINSERT\s+OR\s+IGNORE\s+INTO\b', 'INSERT INTO', query, flags=re.IGNORECASE)
            if "ON CONFLICT" not in q_upper:
                query = query + " ON CONFLICT DO NOTHING"
        elif "INSERT OR REPLACE" in q_upper:
            query = re.sub(r'\bINSERT\s+OR\s+REPLACE\s+INTO\b', 'INSERT INTO', query, flags=re.IGNORECASE)
            if "INTO BLACKLIST" in q_upper:
                query = query + " ON CONFLICT (user_id) DO UPDATE SET expires_at = EXCLUDED.expires_at, reason = EXCLUDED.reason"
            elif "INTO AFK" in q_upper:
                query = query + " ON CONFLICT (server_id, user_id) DO UPDATE SET reason = EXCLUDED.reason, timestamp = EXCLUDED.timestamp"
            else:
                query = query + " ON CONFLICT DO NOTHING"

        # Parameter Placeholder Translation (? -> %s)
        query = query.replace("?", "%s")
        return query

    def execute(self, query, params=None):
        translated = self._translate_query(query)
        if translated is None:
            return self
        if params is not None:
            self._cursor.execute(translated, params)
        else:
            self._cursor.execute(translated)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        if size is None:
            return self._cursor.fetchmany()
        return self._cursor.fetchmany(size)

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)

class PostgresConnection:
    def __init__(self, db_url):
        self._conn = psycopg2.connect(db_url)
        self._conn.autocommit = True

    def cursor(self):
        return PostgresCursor(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

def connect(db_path="warnings.db", **kwargs):
    """
    Universal Database Connection Engine.
    - Agar DATABASE_URL configured hai aur psycopg2 installed hai -> PostgreSQL connection deta hai.
    - Warna -> SQLite local db file (warnings.db) connection deta hai.
    """
    db_url = get_database_url()
    if db_url and HAS_PSYCOPG2:
        try:
            return PostgresConnection(db_url)
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed ({e}). Falling back to SQLite ({db_path}).")
            return _sqlite3.connect(db_path, check_same_thread=False, timeout=20.0, isolation_level=None)
    return _sqlite3.connect(db_path, check_same_thread=False, timeout=20.0, isolation_level=None)
