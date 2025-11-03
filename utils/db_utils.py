import sqlite3

DB_PATH = 'db/my_database.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def fetch_all(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_users():
    query = 'SELECT id, login, email FROM users'
    return fetch_all(query)

