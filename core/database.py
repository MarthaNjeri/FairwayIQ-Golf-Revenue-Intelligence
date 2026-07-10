import sqlite3
import os

DB_PATH = "data/fairway_iq.db"

def init_db():
    """Initializes the relational database schema if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable foreign key support in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Society Configuration Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS society_settings (
        society_id TEXT PRIMARY KEY,
        society_name TEXT NOT NULL,
        tournament_format TEXT DEFAULT 'Match Play - Net',
        points_win INTEGER DEFAULT 3,
        points_draw INTEGER DEFAULT 1,
        points_loss INTEGER DEFAULT 0,
        player_directory_mode TEXT DEFAULT 'Seasonal'
    );
    """)
    
    # 2. Transient Seasonal Roster Table (Solves fluid roster requirements)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS seasonal_roster (
        player_id TEXT PRIMARY KEY,
        society_id TEXT,
        season_id TEXT NOT NULL,
        player_name TEXT NOT NULL,
        handicap REAL NOT NULL,
        checked_in INTEGER DEFAULT 0,
        FOREIGN KEY (society_id) REFERENCES society_settings(society_id) ON DELETE CASCADE
    );
    """)
    
    # 3. Relational Scorecards Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scorecards (
        card_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id TEXT,
        gross_score INTEGER NOT NULL,
        net_score REAL NOT NULL,
        format_played TEXT NOT NULL,
        marker_name TEXT NOT NULL,
        play_date TEXT NOT NULL,
        FOREIGN KEY (player_id) REFERENCES seasonal_roster(player_id)
    );
    """)
    
    # Seed a default sample society row for testing if table is entirely bare
    cursor.execute("SELECT COUNT(*) FROM society_settings;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO society_settings (society_id, society_name, points_win, points_draw, points_loss)
        VALUES ('Luxe_League_01', 'Limuru Golf Society', 3, 1, 0);
        """)
        
    conn.commit()
    conn.close()

def get_db_connection():
    """Returns a thread-safe connection instance to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name like dictionary items
    return conn