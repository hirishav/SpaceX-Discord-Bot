# database.py - Reverted to Pure SQLite
import sqlite3

# Re-export sqlite3 exceptions and attributes for compatibility
Error = sqlite3.Error
OperationalError = sqlite3.OperationalError
IntegrityError = sqlite3.IntegrityError
DatabaseError = sqlite3.DatabaseError

def connect(db_path="warnings.db", **kwargs):
    """
    Standard SQLite Connection.
    """
    return sqlite3.connect(db_path, check_same_thread=False, timeout=20.0, isolation_level=None)
