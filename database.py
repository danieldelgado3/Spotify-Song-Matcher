import sqlite3

def get_db():
    return sqlite3.connect("spotify.db")

def drop_all_tables():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table[0]}")
        conn.commit()

def create_table(username):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f'''CREATE TABLE IF NOT EXISTS user_{username} (
            id INTEGER PRIMARY KEY,
            track_name TEXT,
            artist_name TEXT
        )''')
        conn.commit()

def count_unique_users():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'user_%'")
        tables = cur.fetchall()
    return len(tables)

def insert_tracks(username, tracks):
    if not username:
        return

    with get_db() as conn:
        cur = conn.cursor()
        for track in tracks:
            cur.execute(f"SELECT id FROM user_{username} WHERE track_name = ? AND artist_name = ?", track)
            existing_track = cur.fetchone()
            if not existing_track:
                cur.execute(f"INSERT INTO user_{username} (track_name, artist_name) VALUES (?, ?)", track)
        conn.commit()
