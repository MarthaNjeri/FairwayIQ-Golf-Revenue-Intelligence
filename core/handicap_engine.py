from core.database import get_db_connection

def get_lcc_course_options():
    """
    Returns available LCC course configurations mapped from official WHS charts.
    """
    return {
        "Simba - Men (Course 1)": {
            "course_id": "SIMBA_MEN",
            "gender": "Men",
            "course_name": "Simba",
            "rating": 72.3,
            "slope": 132,
            "par": 72
        },
        "Chui - Men (Course 2)": {
            "course_id": "CHUI_MEN",
            "gender": "Men",
            "course_name": "Chui",
            "rating": 66.7,
            "slope": 119,
            "par": 72
        },
        "Simba - Women (Course 1)": {
            "course_id": "SIMBA_WOMEN",
            "gender": "Women",
            "course_name": "Simba",
            "rating": 78.9,
            "slope": 143,
            "par": 72
        },
        "Chui - Women (Course 2)": {
            "course_id": "CHUI_WOMEN",
            "gender": "Women",
            "course_name": "Chui",
            "rating": 71.8,
            "slope": 125,
            "par": 72
        }
    }

def calculate_player_course_handicap(course_key: str, handicap_index: float) -> int:
    """
    Looks up the official Course Handicap based on the selected course key
    and the player's Handicap Index.
    """
    options = get_lcc_course_options()
    if course_key not in options:
        return None
        
    config = options[course_key]
    course_id = config["course_id"]
    gender = config["gender"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT course_handicap FROM course_conversion_brackets
        WHERE course_id = ? AND gender = ? AND ? >= min_index AND ? <= max_index
    '''
    cursor.execute(query, (course_id, gender, handicap_index, handicap_index))
    result = cursor.fetchone()
    conn.close()
    
    return result["course_handicap"] if result else None


def validate_player_eligibility(player_id: str, handicap_index: float) -> dict:
    """
    Evaluates whether a player is eligible to play under the club's event rules 
    and WHS compliance thresholds (e.g., max 54.0 handicap index limit).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT membership_status, is_eligible, review_reason 
        FROM player_eligibility_status WHERE player_id = ?
    ''', (player_id,))
    record = cursor.fetchone()
    conn.close()
    
    status = "Member"
    is_eligible = True
    reason = "Verified member profile"
    
    if record:
        status = record["membership_status"]
        is_eligible = bool(record["is_eligible"])
        reason = record["review_reason"] or "Passed eligibility check"
        
    # Standard WHS maximum limit safeguard
    if handicap_index > 54.0:
        is_eligible = False
        reason = "Handicap Index exceeds the WHS maximum limit of 54.0"

    return {
        "player_id": player_id,
        "membership_status": status,
        "is_eligible": is_eligible,
        "status_message": reason
    }