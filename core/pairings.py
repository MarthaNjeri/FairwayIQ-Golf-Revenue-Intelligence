import sqlite3
import random
from core.database import DB_PATH

def generate_round_pairings(round_id, season_id):
    """
    Fetches all checked-in players for the active season, 
    shuffles them, and pairs them up head-to-head for the specified round.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fetch only checked-in players
    cursor.execute("""
        SELECT id, name FROM players 
        WHERE season_id = ? AND checked_in = 1
    """, (season_id,))
    players = cursor.fetchall() # Returns list of tuples: (id, name)
    
    if len(players) < 2:
        conn.close()
        return "Error: Not enough checked-in players to generate matches."
    
    # Shuffle players to randomize match-ups
    random.shuffle(players)
    
    # Clear any existing pairings for this round to avoid duplicates
    cursor.execute("DELETE FROM matches WHERE round_id = ?", (round_id,))
    
    pairings_created = 0
    # Pair them up in twos
    for i in range(0, len(players) - 1, 2):
        p1 = players[i]
        p2 = players[i+1]
        
        cursor.execute("""
            INSERT INTO matches (round_id, player_1_id, player_2_id)
            VALUES (?, ?, ?)
        """, (round_id, p1[0], p2[0]))
        pairings_created += 1
    
    # Handle odd number of players (Bye Round logic)
    if len(players) % 2 != 0:
        odd_player = players[-1]
        print(f"Notice: {odd_player[1]} gets a bye this round.")
        # We can record a dummy match or log a Bye in a separate table/status
        
    conn.commit()
    conn.close()
    return f"Successfully generated {pairings_created} head-to-head matches!"