from flask import Flask, render_template, request, redirect, url_for
import os, json, subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
HLS_FOLDER = 'static/hls'
VIDEO_DB = 'videos.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダ作成（なければ）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(HLS_FOLDER, exist_ok=True)

# JSON初期化
if not os.path.exists(VIDEO_DB):
    with open(VIDEO_DB, 'w') as f:
        json.dump([], f)

@app.route('/')
def index():
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    return render_template('index.html', videos=videos)

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
                'title': title,
                'description': description,
                'thumbnail': thumbnail_filename,
                'hls_path': f"{basename}/playlist.m3u8"
            })

            with open(VIDEO_DB, 'w') as f:
                json.dump(videos, f, indent=2)

            return redirect(url_for('index'))

    return render_template('upload.html')
