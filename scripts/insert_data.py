from utils.db_utils import execute_query

def add_user(login, email, password):
    query = '''
    INSERT INTO users (login, email, password)
    VALUES (?, ?, ?)
    '''
    execute_query(query, (login, email, password))
    print(f"Пользователь {login} добавлен.")

# Пример вызова
add_user('liza', 'liza@example.com', 'securepassword123')
