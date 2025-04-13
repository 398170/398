from flask import Flask, render_template, request, redirect, url_for, session
import json, os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # セッション管理のためのシークレットキー

# フォルダ設定
UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
VIDEO_DB = 'videos.json'
USER_DB = 'users.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダ作成（なければ）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

# JSON初期化
if not os.path.exists(VIDEO_DB):
    with open(VIDEO_DB, 'w') as f:
        json.dump([], f)

if not os.path.exists(USER_DB):
    with open(USER_DB, 'w') as f:
        json.dump([], f)

# ユーザー用クラス
class User:
    def __init__(self, id, username, password, is_admin=False):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

# トップページ
@app.route('/')
def index():
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    return render_template('index.html', videos=videos)

# ユーザー登録ページ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin', False)

        hashed_password = generate_password_hash(password, method='sha256')

        # 新しいユーザーを登録
        with open(USER_DB, 'r') as f:
            users = json.load(f)

        new_user = {
            'id': len(users) + 1,  # ユーザーIDは単純にデータベースの長さで決める
            'username': username,
            'password': hashed_password,
            'is_admin': is_admin
        }

        users.append(new_user)

        with open(USER_DB, 'w') as f:
            json.dump(users, f, indent=2)

        return redirect(url_for('login'))

    return render_template('register.html')

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ユーザー情報をデータベースから取得
        with open(USER_DB, 'r') as f:
            users = json.load(f)

        user = next((u for u in users if u['username'] == username), None)

        if user and check_password_hash(user['password'], password):
            # ユーザーが見つかり、パスワードが正しければ
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']

            return redirect(url_for('index'))

        return 'ログイン失敗'

    return render_template('login.html')

# ログアウト処理
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 動画アップロード
@app.route('/upload', methods=['GET', 'POST'])
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

            # 保存
            with open(VIDEO_DB, 'r') as f:
                videos = json.load(f)

            videos.append({
                'title': title,
                'description': description,
                'filename': filename,
                'thumbnail': thumbnail_filename
            })

            with open(VIDEO_DB, 'w') as f:
                json.dump(videos, f, indent=2)

            return redirect(url_for('index'))

    return render_template('upload.html')

# 動画削除（管理者用）
@app.route('/delete_video/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    # 管理者だけが削除できるように確認
    if not session.get('is_admin'):
        return '管理者権限が必要です', 403

    # 動画削除の処理（例：動画IDで削除）
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    video_to_delete = next((v for v in videos if v['id'] == video_id), None)

    if video_to_delete:
        videos.remove(video_to_delete)

        with open(VIDEO_DB, 'w') as f:
            json.dump(videos, f, indent=2)

        return redirect(url_for('index'))
    
    return '動画が見つかりませんでした', 404

# 管理者用動画一覧表示
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    return render_template('admin.html', videos=videos)

# サーバー起動
if __name__ == '__main__':
    app.run(debug=True)
