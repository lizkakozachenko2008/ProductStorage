from utils.db_utils import fetch_all

def get_all_users():
    query = 'SELECT id, login, email FROM users'
    users = fetch_all(query)
    for user in users:
        print(user)

get_all_users()
