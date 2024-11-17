from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to home after successful login
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')  # Show login form if not POST

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
            return redirect(url_for('login'))  # Redirect to login page after registration
        else:
            flash('Username already taken. Please choose another.', 'danger')

    return render_template('register.html')  # Show registration form if not POST


@app.route('/chat')
def chat():
    cursor = request.args.get('cursor', 0, type=int)
    response = requests.get(f'http://localhost:2020/channels?cursor={cursor}')
    data = response.json()
    channels = data['items']
    next_page = data.get('next')

    return render_template('chat.html', channels=channels, next_page=next_page)

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
