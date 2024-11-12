from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# In-memory 'user database' for demo purposes
users = {"user": "password"}  # Replace with a real user database in production

# Sample list of contacts
contacts = ["Alice", "Bob", "Charlie"]

@app.route('/')
def home():
    # If the user is logged in, show the chat interface
    if 'username' in session:
        return render_template('chat.html', contacts=contacts, username=session['username'])
    return render_template('index.html')  # Show login/register page if not logged in

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

@app.route('/chat/<contact>', methods=['GET', 'POST'])
def chat(contact):
    # Only allow access if logged in
    if 'username' not in session:
        flash('Please log in to access the chat.', 'warning')
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Handle sending messages (this can be extended with a database or other storage)
        message = request.form['message']
        flash(f'Message sent to {contact}: {message}', 'success')
    return render_template('chat.html', contact=contact, username=session['username'])

if __name__ == "__main__":
    app.run(debug=True)
