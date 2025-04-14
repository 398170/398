import os
import json
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
VIDEO_JSON = 'videos.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

@app.route('/')
def index():
    if not os.path.exists(VIDEO_JSON):
        with open(VIDEO_JSON, 'w') as f:
            json.dump([], f)

    with open(VIDEO_JSON, 'r') as f:
        videos = json.load(f)
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']
        if file:
            filename = file.filename
            video_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(video_path)

            # 保存
            video_data = {
                'title': title,
                'description': description,
                'filename': filename
            }

            if os.path.exists(VIDEO_JSON):
                with open(VIDEO_JSON, 'r') as f:
                    videos = json.load(f)
            else:
                videos = []

            videos.append(video_data)
            with open(VIDEO_JSON, 'w') as f:
                json.dump(videos, f, indent=2)

            return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/videos/<filename>')
def video(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/register')
def register():
    return "<h1>準備中の登録ページです</h1>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
