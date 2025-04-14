from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

VIDEO_DATA_FILE = 'videos.json'
USER_DATA_FILE = 'users.json'

# 動画情報を読み込み
def load_videos():
    if not os.path.exists(VIDEO_DATA_FILE):
        return []
    with open(VIDEO_DATA_FILE, 'r') as f:
        return json.load(f)

# ユーザー情報を読み込み
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

# ユーザー情報を保存
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

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        flash('ログインしてください')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']

        if file and file.filename.endswith('.mp4'):
            # ファイル保存先を確保
            if not os.path.exists('static/uploads'):
                os.makedirs('static/uploads')
            filename = file.filename
            save_path = os.path.join('static', 'uploads', filename)
            file.save(save_path)

            # 動画情報を保存
            videos = load_videos()
            videos.append({'title': title, 'description': description, 'filename': filename})
            with open(VIDEO_DATA_FILE, 'w') as f:
                json.dump(videos, f)

            flash('動画をアップロードしました')
            return redirect(url_for('index'))
        else:
            flash('mp4ファイルをアップロードしてください')

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
