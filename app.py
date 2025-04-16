import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import ffmpeg  # ffmpeg-python

app = Flask(__name__)
app.secret_key = os.urandom(24)

# フォルダ設定
UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
HLS_FOLDER = 'static/hls'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['HLS_FOLDER'] = HLS_FOLDER

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
VIDEOS_FILE = 'videos.json'

# ログイン設定
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

users = {'admin': {'password': 'admin'}}

def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_videos(videos):
    with open(VIDEOS_FILE, 'w') as f:
        json.dump(videos, f)

# サムネイル生成
def generate_thumbnail(video_path, thumbnail_path):
    try:
        (
            ffmpeg
            .input(video_path, ss=5)
            .output(thumbnail_path, vframes=1, format='image2')
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg Error:", e.stderr.decode())
        raise RuntimeError("サムネイル生成に失敗しました。")

# HLS変換（動画の最初が切れないように改善）
def convert_to_hls(video_path, video_id):
    hls_path = os.path.join(HLS_FOLDER, video_id)
    os.makedirs(hls_path, exist_ok=True)

    (
        ffmpeg
        .input(video_path)
        .output(
            os.path.join(hls_path, 'index.m3u8'),
            format='hls',
            start_number=0,
            hls_time=4,
            hls_list_size=0,
            hls_segment_filename=os.path.join(hls_path, 'segment_%03d.ts')
        )
        .run(capture_stdout=True, capture_stderr=True)
    )

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, user_id)

@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def video_page(video_id):
    videos = load_videos()
    video = videos[video_id]
    comments = video.get('comments', [])

    if request.method == 'POST':
        if 'comment' in request.form:
            comment = request.form['comment']
            comments.append({'username': current_user.username, 'text': comment})
            video['comments'] = comments
            save_videos(videos)
            flash('コメントを投稿しました！', 'success')

        if 'like' in request.form:
            video['likes'] += 1
            save_videos(videos)
            flash('いいね！', 'success')

    return render_template('video.html', video=video, comments=comments)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video_file = request.files['video']
        tags = request.form['tags'].split(',')

        if video_file and allowed_file(video_file.filename):
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_path)

            thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], f"{filename}.jpg")
            video_id = str(len(load_videos()))

            try:
                generate_thumbnail(video_path, thumbnail_path)
                convert_to_hls(video_path, video_id)
            except Exception as e:
                flash(str(e), 'danger')
                return redirect(url_for('upload'))

            videos = load_videos()
            videos.append({
                'id': int(video_id),
                'title': title,
                'description': description,
                'file': filename,
                'thumbnail': f"{filename}.jpg",
                'comments': [],
                'likes': 0,
                'tags': tags,
                'playlist': []
            })
            save_videos(videos)

            flash('動画がアップロードされました！', 'success')
            return redirect(url_for('index'))
    
    return render_template('upload.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username, username)
            login_user(user)
            flash('ログインしました！', 'success')
            return redirect(url_for('index'))
        flash('無効なユーザー名またはパスワード', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in users:
            users[username] = {'password': password}
            flash('ユーザー登録が完了しました！', 'success')
            return redirect(url_for('login'))
        flash('そのユーザー名はすでに使用されています', 'danger')
    return render_template('register.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    videos = load_videos()
    result = [video for video in videos if query.lower() in video['title'].lower()]
    return render_template('search_results.html', query=query, videos=result)

@app.route('/related_videos/<int:video_id>', methods=['GET'])
def related_videos(video_id):
    videos = load_videos()
    video = videos[video_id]
    related = [v for v in videos if any(tag in video['tags'] for tag in v['tags']) and v['id'] != video_id]
    return render_template('related_videos.html', video=video, related_videos=related)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
