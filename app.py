from flask import Flask, render_template, request, request, redirect, url_for, session, flash, jsonify, make_response
import requests
import json
from flask_socketio import SocketIO, emit
from websocket import create_connection, WebSocketApp
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

socketio = SocketIO(app)

# Example WebSocket client to connect and forward messages to localhost:3333
def websocket_forward():
    def on_message(ws, message):
        print("Received from WebSocket server:", message)
        # Forward the message to WebSocket server running on localhost:3333
        forward_ws.send(message)

    def on_error(ws, error):
        print("Error:", error)

    def on_close(ws, close_status_code, close_msg):
        print("Closed WebSocket connection")

    def on_open(ws):
        print("WebSocket connection opened")

    # Connect to WebSocket server on localhost:3333
    forward_ws = WebSocketApp("ws://localhost:3333/ws", 
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)
    forward_ws.on_open = on_open
    forward_ws.run_forever()

# Start WebSocket forwarding in a separate thread
def start_websocket_forwarding():
    thread = threading.Thread(target=websocket_forward)
    thread.daemon = True
    thread.start()

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

@app.route('/newchannel', methods=['GET', 'POST'])
def newchannel():
    if request.method == 'GET':
        username = request.cookies.get('username')
        jwt = request.cookies.get('jwt')
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
        return render_template('newchannel.html', user=user_data, channels=channels)

    elif request.method == 'POST':
        name = request.form['name']
        is_public = 'is_private' not in request.form
        owner_id = request.form['owner_id']

        response = requests.post('http://localhost:2020/channels/', json={
            'name': name,
            'is_public': is_public,
            'owner_id': owner_id,
            'users_acces': [{'user_id': owner_id, 'is_admin': True, 'can_write': True}]
        })

        if response.status_code == 201:  # Channel created successfully
            response_data = json.loads(response.text)
            return redirect(url_for('chat_channel', uuid=response_data['uuid']))
        else:
            return redirect(url_for('newchannel'))

@app.route('/chat/<uuid>', methods=['GET', 'POST'])
def chat_channel(uuid):
    # Fetch channels
    cursor = request.args.get('cursor', 0, type=int)
    response = requests.get(f'http://localhost:2020/channels?cursor={cursor}')
    data = response.json()
    channels = data['items']
    next_page = data.get('next')

    # Fetch current channel details
    response = requests.get(f'http://localhost:2020/channels/{uuid}')
    current_channel = response.json()

    # Fetch messages for the channel
    response = requests.get(f'http://localhost:2020/messages/channel/{uuid}')
    messages = response.json().get('items', [])
    
    # Fetch user data for each message
    
    # Fetch user data and update the messages directly
    seen_users = {}
    if messages is not None:
        for i in range(len(messages)):
            user_id = messages[i]['UserID']
            if user_id not in seen_users:  # Avoid duplicate requests for the same user
                user_response = requests.get(f'http://localhost:2020/users/{user_id}')
                if user_response.status_code == 200:
                    seen_users[user_id] = user_response.json().get('username', 'Unknown')
                else:
                    seen_users[user_id] = 'Unknown'
            # Update the message with the username
            messages[i]['username'] = seen_users[user_id]

    # Handle form submission for sending a new message
    if request.method == 'POST':
        url = "http://localhost:2020/messages"
        payload = {
            "channel_id": uuid,
            "user_id": request.json['user_id'],
            "message": request.json['message']
        }
        response = requests.post(url, json=payload)
        return jsonify({}), 201

    return render_template(
        'chat.html',
        uuid=uuid,
        channels=channels,
        current_channel=current_channel,
        messages=messages
    )


if __name__ == "__main__":
    # app.run(debug=True)
    start_websocket_forwarding()  # Start forwarding to WebSocket server
    socketio.run(app, debug=True)
