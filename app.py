from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

VIDEO_DATA_FILE = 'videos.json'
USER_DATA_FILE = 'users.json'

def load_videos():
    if not os.path.exists(VIDEO_DATA_FILE):
        return []
    with open(VIDEO_DATA_FILE, 'r') as f:
        return json.load(f)

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            flash('すでに登録されています')
        else:
            users[username] = password
            save_users(users)
            flash('登録が完了しました。ログインしてください。')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and users[username] == password:
            session['username'] = username
            flash('ログインしました')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが違います')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('ログアウトしました')
    return redirect(url_for('index'))

# Render用にポートとホストを指定して起動
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
