import sqlite3
import streamlit as st
from pathlib import Path

# variable to store database's location
_db_path = str(Path(__file__).parent.parent.parent / "data.db")

# _db_path and _get_connection are created with _ at the start which means they are created and work only within this file internally...can't use them anywhere else

@st.cache_resource   # tells streamlit to create this once and reuse it 

def _get_connection():  # defines a function that returns a database connection.
    conn = sqlite3.connect(_db_path, check_same_thread = False) # Streamlit uses multiple thread so "check_same_thread" allows the same database connection to be used from multiple threads instead of only the thread that created it.
    conn.row_factory = sqlite3.Row  # make results accessible like dictionaries
    return conn  # returns database connection object   

def init_db():   # function to create database tables if they don't exist yet. Runs only once
    conn = _get_connection()   # gets the database connection

    with conn:      # performs database operations safely and automatically saves changes when finished instead of doing conn.commit() manually 
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercises(
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT NOT NULL,
                reps          INTEGER NOT NULL DEFAULT 0, 
                sets          INTEGER NOT NULL DEFAULT 0, 
                time          INTEGER NOT NULL DEFAULT 0, 
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fatigue_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)
        
        try:
            conn.execute("ALTER TABLE exercises ADD COLUMN form_score REAL DEFAULT 0")
        except:
            pass
        
# authentication related functions

def get_user(username):
    conn = _get_connection()

    return conn.execute("""
        SELECT * FROM users WHERE username = ?
    """, (username,)).fetchone()    # fetchone() - Gets and returns only one row/result from the query.

def create_user(username):
    conn = _get_connection()

    with conn:
        conn.execute("""
            INSERT INTO users (username) VALUES (?)
    """, (username,))
        
    return get_user(username)

def get_or_create_user(username):
    user = get_user(username)  # get the user first

    if user is None:           # if user doesn't exist, create the user
        user = create_user(username)
    
    return user    # if the user exists, return the user value

# function to store workout data
def add_exercise(user_id, exercise_name, reps, sets, time):
    conn = _get_connection()

    with conn:
        existing = conn.execute("""
            SELECT * FROM exercises WHERE
            user_id = ? AND exercise_name = ? AND Date(created_at) = Date('now')
    """, (user_id, exercise_name)).fetchone()
        
        if existing:
            conn.execute("""
                UPDATE exercises
                SET reps = reps + ?, sets = sets + ?, time = time + ?
                WHERE id = ?
    """, (reps, sets, time, existing['id']))
            
        else:
            conn.execute("""
                INSERT INTO exercises (user_id, exercise_name, sets, reps, time)
                VALUES (?, ?, ?, ?, ?)
    """,(user_id, exercise_name, sets, reps, time))
            
# tracking form score
            
def save_form_score(user_id, exercise_name, score):
    conn = _get_connection()

    with conn:
        conn.execute("""
            UPDATE exercises
            SET form_score = ?
            WHERE user_id = ? AND exercise_name = ? AND Date(created_at) = Date('now')
    """, (score, user_id, exercise_name))
        
# fatigue detection
def fatigue_detection(user_id, exercise_name):
    conn = _get_connection()

    with conn:
        conn.execute("""
            INSERT INTO fatigue_events (user_id, exercise_name, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)""", 
            (user_id, exercise_name))

# fatigue history for the user
def get_fatigue_events(user_id):
    conn = _get_connection()

    return conn.execute("""
        SELECT exercise_name, created_at
        FROM fatigue_events
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
        
# Session-aware LLM Coaching
def get_recent_sessions(user_id, limit=5):
    conn = _get_connection()

    return conn.execute("""
        SELECT exercise_name, reps, sets, time, form_score, created_at 
        FROM exercises 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()

# progress trends
def get_exercise_progress(user_id, exercise_name):
    conn = _get_connection()
    
    return conn.execute("""
        SELECT reps, sets, form_score, created_at 
        FROM exercises 
        WHERE user_id = ? AND exercise_name = ?
        ORDER BY created_at ASC
    """, (user_id, exercise_name)).fetchall()
            
#fcn to display the database on the dashboard
def get_users_exercises(user_id):
    conn = _get_connection()

    return conn.execute("""
        SELECT * FROM exercises
        WHERE user_id = ?
    """, (user_id,)).fetchall()   # fetchall() - Gets and returns all rows/results from the query.