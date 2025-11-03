import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_utils import fetch_all, execute_query

# Проверка таблицы
tables = fetch_all('SELECT name FROM sqlite_master WHERE type="table" AND name="users"')
print("✅ Таблица users найдена." if tables else "❌ Таблица users НЕ найдена.")

# Вставка
execute_query('INSERT INTO users (login, email, password) VALUES (?, ?, ?)', ('test', 'test@example.com', '123'))
print("✅ Пользователь test добавлен.")

# Чтение
users = fetch_all('SELECT login, email FROM users')
print("📋 Список пользователей:")
for u in users:
    print(u)

# Удаление
execute_query('DELETE FROM users WHERE login = ?', ('test',))
print("🗑️ Пользователь test удалён.")
