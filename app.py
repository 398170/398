import json
import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

# アップロードされたファイルを保存する場所
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}

# 動画メタデータ保存先
VIDEO_DB = 'videos.json'

# アップロードされたファイルが許可された拡張子か確認する関数
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# サムネイル生成関数
def generate_thumbnail(video_path, thumbnail_path):
    """動画からサムネイルを生成する"""
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-ss', '00:00:05.000',
        '-vframes', '1',
        '-q:v', '2',
        thumbnail_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# アップロード処理
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            video_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(video_path)

            # 動画ID取得
            with open(VIDEO_DB, 'r') as f:
                videos = json.load(f)
            video_id = len(videos)

            # サムネイルを生成
            thumbnail_filename = f'{video_id}.jpg'
            thumbnail_path = os.path.join('static', 'thumbnails', thumbnail_filename)
            generate_thumbnail(video_path, thumbnail_path)

            # メタデータ保存
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

# トップページの処理
@app.route('/')
def index():
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    return render_template('index.html', videos=videos)

if __name__ == '__main__':
    app.run(debug=True)
