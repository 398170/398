from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os, json, subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'your_secret_key'

# Flask-Loginの設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
HLS_FOLDER = 'static/hls'
VIDEO_DB = 'videos.json'
USER_DB = 'users.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダ作成（なければ）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(HLS_FOLDER, exist_ok=True)

# ユーザーデータの初期化
if not os.path.exists(USER_DB):
    with open(USER_DB, 'w') as f:
        json.dump([], f)

# 動画のメタデータ
if not os.path.exists(VIDEO_DB):
    with open(VIDEO_DB, 'w') as f:
        json.dump([], f)

# Userクラスの定義
class User(UserMixin):
    def __init__(self, id, username, password, is_admin=False):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

# ユーザーのロード
@login_manager.user_loader
def load_user(user_id):
    with open(USER_DB, 'r') as f:
        users = json.load(f)
    for user in users:
        if user['id'] == user_id:
            return User(user['id'], user['username'], user['password'], user['is_admin'])
    return None

# 管理者のみのアクセスを制限するカスタムデコレータ
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash('管理者のみのアクセスです。')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ルート：ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open(USER_DB, 'r') as f:
            users = json.load(f)
        for user in users:
            if user['username'] == username and user['password'] == password:
                user_obj = User(user['id'], user['username'], user['password'], user['is_admin'])
                login_user(user_obj)
                return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

# ルート：ログアウト
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# ルート：登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'  # 管理者チェック
        with open(USER_DB, 'r') as f:
            users = json.load(f)
        new_user = {
            'id': len(users) + 1,
            'username': username,
            'password': password,
            'is_admin': is_admin
        }
        users.append(new_user)
        with open(USER_DB, 'w') as f:
            json.dump(users, f)
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# 動画一覧ページ
@app.route('/')
def index():
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    return render_template('index.html', videos=videos)

# アップロード機能
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']

        if file:
            filename = secure_filename(file.filename)
            basename = filename.rsplit('.', 1)[0]
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            # サムネイル作成
            thumbnail_filename = basename + '.jpg'
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
            subprocess.run([
                'ffmpeg', '-i', upload_path,
                '-ss', '00:00:01.000', '-vframes', '1',
                thumbnail_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # HLS変換
            hls_output_dir = os.path.join(HLS_FOLDER, basename)
            os.makedirs(hls_output_dir, exist_ok=True)
            subprocess.run([
                'ffmpeg', '-i', upload_path,
                '-codec:', 'copy',
                '-start_number', '0',
                '-hls_time', '10',
                '-hls_list_size', '0',
                '-f', 'hls',
                os.path.join(hls_output_dir, 'playlist.m3u8')
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 保存
            with open(VIDEO_DB, 'r') as f:
                videos = json.load(f)

            videos.append({
                'id': len(videos) + 1,
                'title': title,
                'description': description,
                'thumbnail': thumbnail_filename,
                'hls_path': f"{basename}/playlist.m3u8",
                'comments': []
            })

            with open(VIDEO_DB, 'w') as f:
                json.dump(videos, f, indent=2)

            return redirect(url_for('index'))

    return render_template('upload.html')

# コメント投稿機能
@app.route('/comment/<video_id>', methods=['POST'])
@login_required
def comment(video_id):
    comment_text = request.form['comment']
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    
    # コメントの追加
    for video in videos:
        if video['id'] == int(video_id):
            video['comments'].append({
                'user': current_user.username,
                'text': comment_text
            })
    
    # 保存
    with open(VIDEO_DB, 'w') as f:
        json.dump(videos, f, indent=2)

    return redirect(url_for('index'))

# 動画削除機能（管理者のみ）
@app.route('/delete_video/<video_id>', methods=['POST'])
@login_required
@admin_required
def delete_video(video_id):
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    
    videos = [video for video in videos if video['id'] != int(video_id)]
    
    with open(VIDEO_DB, 'w') as f:
        json.dump(videos, f, indent=2)

    flash('動画が削除されました。')
    return redirect(url_for('index'))

# コメント削除機能（管理者のみ）
@app.route('/delete_comment/<video_id>/<comment_user>', methods=['POST'])
@login_required
@admin_required
def delete_comment(video_id, comment_user):
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    
    for video in videos:
        if video['id'] == int(video_id):
            video['comments'] = [comment for comment in video['comments'] if comment['user'] != comment_user]
    
    with open(VIDEO_DB, 'w') as f:
        json.dump(videos, f, indent=2)

    flash('コメントが削除されました。')
    return redirect(url_for('index'))
