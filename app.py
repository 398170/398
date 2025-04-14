from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# JSONファイルのパス
VIDEO_DATA_FILE = 'videos.json'
USER_DATA_FILE = 'users.json'

# アップロード保存先
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 動画データの読み書き
def load_videos():
    if not os.path.exists(VIDEO_DATA_FILE):
        return []
    with open(VIDEO_DATA_FILE, 'r') as f:
        return json.load(f)

def save_videos(videos):
    with open(VIDEO_DATA_FILE, 'w') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

# ユーザーデータの読み書き
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# トップページ
@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

# ユーザー登録
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

# ログイン
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

# ログアウト
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('ログアウトしました')
    return redirect(url_for('index'))

# 動画アップロード
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        flash('ログインしてください')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']

        if file:
            filename = file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            videos = load_videos()
            videos.append({
                'title': title,
                'description': description,
                'filename': filename,
                'uploader': session['username']
            })
            save_videos(videos)

            flash('動画をアップロードしました')
            return redirect(url_for('index'))

    return render_template('upload.html')

# アプリ実行（Render対応）
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
