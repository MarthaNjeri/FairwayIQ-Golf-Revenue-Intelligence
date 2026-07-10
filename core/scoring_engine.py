import sqlite3
import pandas as pd
from datetime import datetime

def seed_seasonal_roster(season_id: str, df_roster: pd.DataFrame, conn: sqlite3.Connection) -> bool:
    """
    Accepts a DataFrame with ['player_name', 'handicap'] columns, 
    appends the active season_id, and safely batch inserts into the database.
    """
    try:
        # Standardize casing to match table schema strings safely
        df_roster.columns = df_roster.columns.str.lower()
        
        # Validate required data structure
        required_cols = {"player_name", "handicap"}
        if not required_cols.issubset(df_roster.columns):
            return False
            
        # Inject the active contextual target season ID & default values
        df_roster["season_id"] = season_id
        df_roster["checked_in"] = 0  # Default check-in state to No
        df_roster["society_id"] = "Luxe_League_01"  # Link directly to your test tenant ID
        
        # Batch append records directly to the SQLite seasonal_roster table
        df_roster.to_sql("seasonal_roster", conn, if_exists="append", index=False)
        return True
    except Exception as e:
        print(f"Database insertion failed: {e}")
        return False


def submit_scorecard(conn: sqlite3.Connection, player_id: str, gross_score: int, handicap: float, format_played: str, marker_name: str) -> bool:
    """
    Inserts a verified scorecard entry into the ledger and transitions 
    the player's active timeline state (checked_in = 2 means round complete).
    """
    cursor = conn.cursor()
    net_score = gross_score - handicap
    play_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # 1. Insert execution straight into the relational Scorecards Table
        cursor.execute("""
            INSERT INTO scorecards (player_id, gross_score, net_score, format_played, marker_name, play_date)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (player_id, gross_score, net_score, format_played, marker_name, play_date))
        
        # 2. State-machine update: flag the player as round finalized
        cursor.execute("""
            UPDATE seasonal_roster 
            SET checked_in = 2 
            WHERE player_id = ?;
        """, (player_id,))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database scorecard submission error: {e}")
        conn.rollback()
        return False


def fetch_league_table(conn: sqlite3.Connection, season_id: str) -> pd.DataFrame:
    """
    Executes a clean analytical aggregation matrix query directly via SQL 
    to compile real-time society standings sorted by your 3-1-0 points layout rules.
    """
    query = """
        SELECT 
            sr.player_name AS Golfer,
            COUNT(s.card_id) AS RoundsPlayed,
            SUM(CASE WHEN s.net_score < 72 THEN 1 ELSE 0 END) AS Wins,
            SUM(CASE WHEN s.net_score = 72 THEN 1 ELSE 0 END) AS Draws,
            SUM(CASE WHEN s.net_score > 72 THEN 1 ELSE 0 END) AS Losses,
            SUM(
                CASE 
                    WHEN s.net_score < 72 THEN ss.points_win
                    WHEN s.net_score = 72 THEN ss.points_draw
                    ELSE ss.points_loss
                END
            ) AS TotalPoints
        FROM seasonal_roster sr
        JOIN society_settings ss ON sr.society_id = ss.society_id
        LEFT JOIN scorecards s ON sr.player_id = s.player_id
        WHERE sr.season_id = ?
        GROUP BY sr.player_id, sr.player_name
        ORDER BY TotalPoints DESC, Wins DESC;
    """
    try:
        # Pulls data straight from SQL execution layout directly into a Streamlit-ready DataFrame
        df_standings = pd.read_sql_query(query, conn, params=(season_id,))
        return df_standings
    except Exception as e:
        print(f"Failed to fetch league calculations: {e}")
        return pd.DataFrame(columns=["Golfer", "RoundsPlayed", "Wins", "Draws", "Losses", "TotalPoints"])