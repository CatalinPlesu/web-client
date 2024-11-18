from flask import Flask, render_template, request, request, redirect, url_for, session, flash, jsonify
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
    session.pop('username', None)  # Remove the username from the session
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))  # Redirect to home after logout


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username not in users:  # Check if the username already exists
            users[username] = password  # Add new user to the 'database'
            flash('Registration successful! Please log in.', 'success')
            # Redirect to login page after registration
            return redirect(url_for('login'))
        else:
            flash('Username already taken. Please choose another.', 'danger')

    # Show registration form if not POST
    return render_template('register.html')


@app.route('/profile')
def profile():
    username = request.cookies.get('username')
    jwt = request.cookies.get('jwt')

    print(username, jwt)

    if not username or not jwt:
        return render_template('profile.html')

    try:
        response = requests.post(
            "http://localhost:2020/users/auth",
            json={"username": username, "jwt": jwt}
        )
        response.raise_for_status()

        user_data = response.json()
        return render_template('profile.html', user=user_data)
    except requests.RequestException as e:
        print(f"Failed to authenticate user: {e}")
        return render_template('profile.html')


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
