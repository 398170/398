from flask import Flask, render_template, request, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
VIDEO_DATA_FILE = 'videos.json'

# アップロードフォルダ作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# JSON初期化（なければ）
if not os.path.exists(VIDEO_DATA_FILE):
    with open(VIDEO_DATA_FILE, 'w') as f:
        json.dump([], f)

# 動画データ読み込み
def load_videos():
    with open(VIDEO_DATA_FILE, 'r') as f:
        return json.load(f)

# 動画データ保存
def save_videos(videos):
    with open(VIDEO_DATA_FILE, 'w') as f:
        json.dump(videos, f, indent=2)

@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['POST'])
def upload():
    videos = load_videos()

    # URL投稿
    video_url = request.form.get('video_url')
    if video_url:
        videos.append({'type': 'url', 'url': video_url})
        save_videos(videos)
        return redirect(url_for('index'))

    # ファイルアップロード
    file = request.files.get('video_file')
    if file and file.filename:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        videos.append({'type': 'file', 'filename': filename})
        save_videos(videos)

    return redirect(url_for('index'))

@app.route('/watch/<int:video_id>')
def watch(video_id):
    videos = load_videos()
    if 0 <= video_id < len(videos):
        return render_template('watch.html', video=videos[video_id])
    return 'Video not found', 404
