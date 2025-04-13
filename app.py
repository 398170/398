from flask import Flask, render_template, request, redirect, url_for, session
import os, json, subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secretkey'  # セッション用

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
HLS_FOLDER = 'static/hls'
VIDEO_DB = 'videos.json'
USERS_DB = 'users.json'
COMMENTS_DB = 'comments.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダ作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(HLS_FOLDER, exist_ok=True)

# JSON初期化
for db in [VIDEO_DB, USERS_DB, COMMENTS_DB]:
    if not os.path.exists(db):
        with open(db, 'w') as f:
            json.dump([], f)

# --------------------------------
# ルーティング
# --------------------------------

@app.route('/')
def index():
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']

        if file:
            filename = secure_filename(file.filename)
            basename = filename.rsplit('.', 1)[0]
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            # サムネイル生成
            thumbnail_filename = basename + '.jpg'
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
            subprocess.run(['ffmpeg', '-i', upload_path, '-ss', '00:00:01.000', '-vframes', '1', thumbnail_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # HLS変換
            hls_output_dir = os.path.join(HLS_FOLDER, basename)
            os.makedirs(hls_output_dir, exist_ok=True)
            subprocess.run([
                'ffmpeg', '-i', upload_path,
                '-codec:', 'copy', '-start_number', '0',
                '-hls_time', '10', '-hls_list_size', '0', '-f', 'hls',
                os.path.join(hls_output_dir, 'playlist.m3u8')
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 保存
            with open(VIDEO_DB, 'r') as f:
                videos = json.load(f)

            videos.append({
                'title': title,
                'description': description,
                'thumbnail': thumbnail_filename,
                'hls_path': f"{basename}/playlist.m3u8",
                'uploader': session['username']
            })

            with open(VIDEO_DB, 'w') as f:
                json.dump(videos, f, indent=2)

            return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/video/<int:index>', methods=['GET', 'POST'])
def video(index):
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    with open(COMMENTS_DB, 'r') as f:
        comments = json.load(f)

    video = videos[index]
    video_comments = [c for c in comments if c['video_index'] == index]

    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('login'))
        comment = request.form['comment']
        comments.append({
            'video_index': index,
            'user': session['username'],
            'text': comment
        })
        with open(COMMENTS_DB, 'w') as f:
            json.dump(comments, f, indent=2)
        return redirect(url_for('video', index=index))

    return render_template('video.html', video=video, index=index, comments=video_comments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with open(USERS_DB, 'r') as f:
            users = json.load(f)

        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                session['is_admin'] = user.get('is_admin', False)
                return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = 'is_admin' in request.form

        with open(USERS_DB, 'r') as f:
            users = json.load(f)

        users.append({'username': username, 'password': password, 'is_admin': is_admin})

        with open(USERS_DB, 'w') as f:
            json.dump(users, f, indent=2)

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/delete_video/<int:index>')
def delete_video(index):
    if not session.get('is_admin'):
        return "管理者のみ削除可能", 403

    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    if index < len(videos):
        del videos[index]
        with open(VIDEO_DB, 'w') as f:
            json.dump(videos, f, indent=2)

    return redirect(url_for('index'))

@app.route('/delete_comment/<int:index>')
def delete_comment(index):
    if not session.get('is_admin'):
        return "管理者のみ削除可能", 403

    with open(COMMENTS_DB, 'r') as f:
        comments = json.load(f)

    if index < len(comments):
        del comments[index]
        with open(COMMENTS_DB, 'w') as f:
            json.dump(comments, f, indent=2)

    return redirect(url_for('index'))

# --------------------------------
# Render 対応のポートバインド
# --------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
