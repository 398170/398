from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os, json, subprocess

app = Flask(__name__)
app.secret_key = 'secretkey'

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
HLS_FOLDER = 'static/hls'
VIDEO_DB = 'videos.json'
USER_DB = 'users.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダ作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(HLS_FOLDER, exist_ok=True)

# JSON初期化
for db in [VIDEO_DB, USER_DB]:
    if not os.path.exists(db):
        with open(db, 'w') as f:
            json.dump([], f)

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
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(upload_path)

            # サムネイル
            thumbnail_filename = basename + '.jpg'
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
            subprocess.run(['ffmpeg', '-i', upload_path, '-ss', '00:00:01.000', '-vframes', '1', thumbnail_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # HLS
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open(USER_DB, 'r') as f:
            users = json.load(f)

        for user in users:
            if user['username'] == username:
                return "ユーザー名は既に使われています"

        users.append({'username': username, 'password': password})
        with open(USER_DB, 'w') as f:
            json.dump(users, f, indent=2)

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open(USER_DB, 'r') as f:
            users = json.load(f)

        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))

        return "ログイン失敗"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def view_video(video_id):
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    if video_id < 0 or video_id >= len(videos):
        return "動画が見つかりません", 404

    video = videos[video_id]

    comments_file = f'comments_{video_id}.json'
    if os.path.exists(comments_file):
        with open(comments_file, 'r') as f:
            comments = json.load(f)
    else:
        comments = []

    if request.method == 'POST':
        comment_text = request.form['comment']
        username = session.get('username', '匿名')
        comments.append({'user': username, 'text': comment_text})
        with open(comments_file, 'w') as f:
            json.dump(comments, f, indent=2)
        return redirect(url_for('view_video', video_id=video_id))

    is_admin = session.get('username') == 'admin'
    return render_template('video.html', video=video, comments=comments, video_id=video_id, is_admin=is_admin)

@app.route('/delete_video/<int:video_id>')
def delete_video(video_id):
    if session.get('username') != 'admin':
        return "管理者のみ削除できます", 403

    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    if video_id < 0 or video_id >= len(videos):
        return "動画が見つかりません", 404

    del videos[video_id]
    with open(VIDEO_DB, 'w') as f:
        json.dump(videos, f, indent=2)

    comments_file = f'comments_{video_id}.json'
    if os.path.exists(comments_file):
        os.remove(comments_file)

    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
