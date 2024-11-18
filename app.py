from flask import Flask, render_template, request, request, redirect, url_for, session, flash, jsonify, make_response
import requests
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# In-memory 'user database' for demo purposes
users = {"user": "password"}  # Replace with a real user database in production

# Example list of contacts (replace with real data if needed)
contacts = ["Alice", "Bob", "Charlie", "David", "Eva"]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        username = request.json['username']
        password = request.json['password']
        response = requests.post('http://localhost:2020/users/login', json={
            'username': username,
            'password': password
        })
        print(response.status_code)
        if response.status_code == 201:
            response_data = json.loads(response.text)

            user = response_data['user']
            jwt = response_data['jwt']

            return jsonify({
                'username': user['username'],
                'user_id': user['user_id'],
                'jwt': jwt
            }), 201
        else:
            return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/logout')
def logout():
    response = make_response(render_template('logout.html'))
    session.pop('username', None)
    response.set_cookie('username', '', expires=0)  # Clear the username cookie
    response.set_cookie('jwt', '', expires=0)  # Clear the JWT cookie
    flash('Logged out successfully.', 'info')
    return response


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()  
        username = data.get('username')
        display_name = data.get('display_name')
        email = data.get('email')
        password = data.get('password')

        # Send a request to the backend API to register the user
        response = requests.post('http://localhost:2020/users/register', json={
            'username': username,
            'display_name': display_name,
            'email': email,
            'password': password
        })
        if response.status_code == 201:  # Success
            response_data = json.loads(response.text)

            user = response_data['user']
            jwt = response_data['jwt']

            return jsonify({
                'username': user['username'],
                'user_id': user['user_id'],
                'jwt': jwt
            }), 201
        else:
            return jsonify({'message': 'Invalid credentials'}), 401

    # If GET method, just render the registration form
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = request.cookies.get('username')
    jwt = request.cookies.get('jwt')

    if not username or not jwt:
        return render_template('profile.html', user=None)

    if request.method == 'GET':
        try:
            cursor = request.args.get('cursor', 0, type=int)
            response = requests.get(f'http://localhost:2020/channels?cursor={cursor}')
            data = response.json()
            channels = data['items']
            next_page = data.get('next')
            response = requests.post(
                "http://localhost:2020/users/auth",
                json={"username": username, "jwt": jwt}
            )
            response.raise_for_status()
            user_data = response.json()
            return render_template('profile.html', user=user_data, channels=channels)

        except requests.RequestException as e:
            print(f"Failed to authenticate or fetch user data: {e}")
            return render_template('profile.html', user=None)

    if request.method == 'POST':
        print('reached post')
        updated_data = request.json
        user_id = updated_data.get('user_id')
        print(request)
        try:
            update_response = requests.put(
                f"http://localhost:2020/users/{user_id}",
                json={
                    "username": updated_data["username"],
                    "display_name": updated_data["display_name"],
                    "email": updated_data["email"],
                    "password": updated_data["password"]
                }
            )

            update_response.raise_for_status()
            return render_template('profile.html', user=updated_data)

        except requests.RequestException as e:
            print(f"Failed to update user data: {e}")
            return render_template('profile.html', user=updated_data)


@app.route('/chat/<uuid>', methods=['GET', 'POST'])
def chat_channel(uuid):
    # Only allow access if logged in
    if 'username' not in session:
        flash('Please log in to access the chat.', 'warning')
        return redirect(url_for('login'))

    cursor = request.args.get('cursor', 0, type=int)
    response = requests.get(f'http://localhost:2020/channels?cursor={cursor}')
    data = response.json()
    channels = data['items']
    next_page = data.get('next')

    if request.method == 'POST':
        # Handle sending messages (this can be extended with a database or other storage)
        message = request.form['message']
        flash(f'Message sent to {channel}: {message}', 'success')

    return render_template('chat.html', uuid=uuid, username=session['username'], channels=channels)


if __name__ == "__main__":
    app.run(debug=True)
