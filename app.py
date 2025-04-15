import os
import uuid
import json
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'secret'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['THUMBNAIL_FOLDER'] = 'static/thumbnails'
app.config['HLS_FOLDER'] = 'static/hls'
app.config['JSON_VIDEOS'] = 'videos.json'
app.config['JSON_USERS'] = 'users.json'
app.config['JSON_COMMENTS'] = 'comments.json'

login_manager = LoginManager()
login_manager.init_app(app)

# ユーザーモデル
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# JSON読み書き
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ルートページ（動画一覧）
@app.route('/')
def index():
    videos = load_json(app.config['JSON_VIDEOS'])
    return render_template('index.html', videos=videos)

# 動画アップロード
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['video']
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags'].split(',')

        if file:
            filename = secure_filename(file.filename)
            uid = str(uuid.uuid4())
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], uid + '_' + filename)
            file.save(video_path)

            # HLS変換
            hls_path = os.path.join(app.config['HLS_FOLDER'], uid)
            os.makedirs(hls_path, exist_ok=True)
            subprocess.call([
                'ffmpeg', '-i', video_path,
                '-codec: copy', '-start_number', '0',
                '-hls_time', '10', '-hls_list_size', '0',
                '-f', 'hls', os.path.join(hls_path, 'index.m3u8')
            ])

            # サムネイル生成
            thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], uid + '.jpg')
            subprocess.call([
                'ffmpeg', '-i', video_path, '-ss', '00:00:01.000', '-vframes', '1', thumbnail_path
            ])

            # メタデータ保存
            videos = load_json(app.config['JSON_VIDEOS'])
            videos.append({
                'id': uid,
                'title': title,
                'description': description,
                'filename': filename,
                'uploader': current_user.id,
                'tags': tags,
                'likes': [],
            })
            save_json(app.config['JSON_VIDEOS'], videos)

            return redirect(url_for('index'))
    return render_template('upload.html')

# 動画再生
@app.route('/video/<video_id>')
def video(video_id):
    videos = load_json(app.config['JSON_VIDEOS'])
    video = next((v for v in videos if v['id'] == video_id), None)
    if video:
        comments = load_json(app.config['JSON_COMMENTS'])
        video_comments = [c for c in comments if c['video_id'] == video_id]
        return render_template('video.html', video=video, comments=video_comments)
    return 'Video not found', 404

# コメント投稿
@app.route('/comment/<video_id>', methods=['POST'])
@login_required
def comment(video_id):
    text = request.form['comment']
    comments = load_json(app.config['JSON_COMMENTS'])
    comments.append({
        'video_id': video_id,
        'user': current_user.id,
        'text': text
    })
    save_json(app.config['JSON_COMMENTS'], comments)
    return redirect(url_for('video', video_id=video_id))

# いいね機能
@app.route('/like/<video_id>')
@login_required
def like(video_id):
    videos = load_json(app.config['JSON_VIDEOS'])
    for video in videos:
        if video['id'] == video_id:
            if current_user.id not in video['likes']:
                video['likes'].append(current_user.id)
            else:
                video['likes'].remove(current_user.id)
            break
    save_json(app.config['JSON_VIDEOS'], videos)
    return redirect(url_for('video', video_id=video_id))

# ユーザー登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_json(app.config['JSON_USERS'])
        if any(u['username'] == username for u in users):
            return 'ユーザー名が既に使われています'
        users.append({'username': username, 'password': password})
        save_json(app.config['JSON_USERS'], users)
        return redirect(url_for('login'))
    return render_template('register.html')

# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_json(app.config['JSON_USERS'])
        for u in users:
            if u['username'] == username and u['password'] == password:
                user = User(username)
                login_user(user)
                return redirect(url_for('index'))
        return 'ログイン失敗'
    return render_template('login.html')

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ポート指定（Render用）
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
