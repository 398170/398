from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg'}
VIDEO_DATA_FILE = 'videos.json'
USER_DATA_FILE = 'users.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダがなければ作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_videos():
    if not os.path.exists(VIDEO_DATA_FILE):
        return []
    with open(VIDEO_DATA_FILE, 'r') as f:
        return json.load(f)

def save_videos(videos):
    with open(VIDEO_DATA_FILE, 'w') as f:
        json.dump(videos, f, indent=2)

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        flash('アップロードにはログインが必要です。')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            videos = load_videos()
            videos.append({
                'title': title,
                'description': description,
                'filename': filename
            })
            save_videos(videos)
            flash('動画をアップロードしました。')
            return redirect(url_for('index'))
        else:
            flash('無効なファイル形式です。対応形式: mp4, webm, ogg')

    return render_template('upload.html')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
