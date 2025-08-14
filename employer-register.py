from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

users = {}

@app.route('/')
def home():
    return render_template('employer-register.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password == confirm_password:
        users[email] = password
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/login')
def login():
    return "Login page (to be added)"

if __name__ == '__main__':
    app.run(debug=True)