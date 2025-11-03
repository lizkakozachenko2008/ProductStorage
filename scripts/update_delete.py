from utils.db_utils import execute_query

def update_password(login, new_password):
    query = 'UPDATE users SET password = ? WHERE login = ?'
    execute_query(query, (new_password, login))
    print(f"Пароль пользователя {login} обновлён.")

def delete_user(login):
    query = 'DELETE FROM users WHERE login = ?'
    execute_query(query, (login,))
    print(f"Пользователь {login} удалён.")

# Примеры вызова
update_password('liza', 'new_secure_password456')
delete_user('liza')
