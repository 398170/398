from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

VIDEO_FOLDER = 'static/videos'
THUMBNAIL_FOLDER = 'static/thumbnails'
VIDEO_DATA_FILE = 'videos.json'
USER_DATA_FILE = 'users.json'
COMMENT_DATA_FILE = 'comments.json'

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

# --- データ読み書き関数 ---
def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_videos():
    return load_json(VIDEO_DATA_FILE, [])

def save_videos(videos):
    save_json(VIDEO_DATA_FILE, videos)

def load_users():
    return load_json(USER_DATA_FILE, {})

def save_users(users):
    save_json(USER_DATA_FILE, users)

def load_comments():
    return load_json(COMMENT_DATA_FILE, {})

def save_comments(comments):
    save_json(COMMENT_DATA_FILE, comments)

# --- ルーティング ---
@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def video(video_id):
    videos = load_videos()
    comments = load_comments()

    video = videos[video_id]
    video_comments = comments.get(str(video_id), [])

    if request.method == 'POST':
        if 'username' not in session:
            flash("コメント投稿にはログインが必要です。")
            return redirect(url_for('login'))
        comment = request.form['comment']
        username = session['username']
        video_comments.append({'user': username, 'text': comment})
        comments[str(video_id)] = video_comments
        save_comments(comments)
        return redirect(url_for('video', video_id=video_id))

    return render_template('video.html', video=video, video_id=video_id, comments=video_comments)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        flash('ログインしてください。')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(VIDEO_FOLDER, filename)
            file.save(filepath)

            videos = load_videos()
            videos.append({
                'title': title,
                'description': description,
                'filename': filename
            })
            save_videos(videos)
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            flash('すでに登録されています。')
        else:
            users[username] = password
            save_users(users)
            flash('登録成功。ログインしてください。')
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
            flash('ログイン成功。')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが違います。')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('ログアウトしました。')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
