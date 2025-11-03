from utils.db_utils import execute_query, fetch_all

def create_users_table():
    query = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    '''
    execute_query(query)
    print("✅ Таблица users создана.")

def insert_user(login, email, password):
    query = '''
    INSERT INTO users (login, email, password)
    VALUES (?, ?, ?)
    '''
    execute_query(query, (login, email, password))
    print(f"✅ Пользователь {login} добавлен.")

def list_users():
    query = 'SELECT id, login, email FROM users'
    users = fetch_all(query)
    print("📋 Список пользователей:")
    for user in users:
        print(user)

def delete_user(login):
    query = 'DELETE FROM users WHERE login = ?'
    execute_query(query, (login,))
    print(f"🗑️ Пользователь {login} удалён.")

# Пример запуска
if __name__ == "__main__":
    create_users_table()
    insert_user('demo', 'demo@example.com', 'pass123')
    list_users()
    delete_user('demo')
