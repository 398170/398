from flask import Flask, render_template, request, redirect, url_for
import os, json, subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
VIDEO_DB = 'videos.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダ作成（なければ）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

# データベース初期化
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # サムネイル作成
            thumbnail_filename = filename.rsplit('.', 1)[0] + '.jpg'
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)

            # FFmpegでサムネイル画像生成（1秒目）
            subprocess.run([
                'ffmpeg',
                '-i', filepath,
                '-ss', '00:00:01.000',
                '-vframes', '1',
                thumbnail_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # JSONに保存
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
