from flask import Flask, request, jsonify
from utils.db_utils import fetch_all, execute_query
from flask_cors import CORS

app = Flask(__name__)

# Настройка CORS: разрешаем только нужные источники и методы
CORS(app, resources={r"/*": {
    "origins": ["http://localhost:8000"],
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "DELETE", "OPTIONS"]
}})

@app.route('/users', methods=['GET'])
def get_users():
    users = fetch_all('SELECT id, login, email FROM users')
    return jsonify(users)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    execute_query('INSERT INTO users (login, email, password) VALUES (?, ?, ?)',
                  (data['login'], data['email'], data['password']))
    return jsonify({'message': 'User added'}), 201

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    execute_query('DELETE FROM users WHERE id = ?', (user_id,))
    return jsonify({'message': 'User deleted'})

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        # Ответ на preflight-запрос
        response = jsonify({'message': 'CORS preflight'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    data = request.get_json()
    login = data.get('login')
    email = data.get('email')
    password = data.get('password')

    if not login or not email or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400

    if fetch_all('SELECT id FROM users WHERE email = ?', (email,)):
        return jsonify({'error': 'Email уже зарегистрирован'}), 409

    execute_query('INSERT INTO users (login, email, password) VALUES (?, ?, ?)', (login, email, password))
    return jsonify({'message': 'Регистрация успешна'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')

    user = fetch_all('SELECT login FROM users WHERE login = ? AND password = ?', (login, password))
    if user:
        return jsonify({'message': f'Добро пожаловать, {user[0][0]}!'})
    else:
        return jsonify({'error': 'Неверный логин или пароль'}), 401

if __name__ == '__main__':
    app.run(debug=True)
