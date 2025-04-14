from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

VIDEO_JSON_FILE = 'videos.json'

# 仮のログインユーザー
logged_in_user = None

# 動画データの読み込み
def load_videos():
    if os.path.exists(VIDEO_JSON_FILE):
        with open(VIDEO_JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    global logged_in_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':
            logged_in_user = username
            flash('ログイン成功！')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名かパスワードが間違っています。')
    return render_template('login.html')

@app.route('/logout')
def logout():
    global logged_in_user
    logged_in_user = None
    flash('ログアウトしました。')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video_data = {
            'title': title,
            'description': description,
            'file': 'sample_video.mp4'
        }
        videos = load_videos()
        videos.append(video_data)
        with open(VIDEO_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=4)
        flash('動画がアップロードされました！')
        return redirect(url_for('index'))
    return render_template('upload.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render.com 用ポート
    app.run(host='0.0.0.0', port=port)
