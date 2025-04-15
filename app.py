import os
import json
import uuid
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
HLS_FOLDER = 'static/hls'
VIDEOS_JSON = 'videos.json'
COMMENTS_JSON = 'comments.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(HLS_FOLDER, exist_ok=True)

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    videos = load_json(VIDEOS_JSON)
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['video']
        if file:
            video_id = str(uuid.uuid4())
            filename = f"{video_id}.mp4"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # サムネイル生成
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, f"{video_id}.jpg")
            subprocess.run(['ffmpeg', '-i', filepath, '-ss', '00:00:01.000', '-vframes', '1', thumbnail_path])

            # HLS変換
            hls_path = os.path.join(HLS_FOLDER, video_id)
            os.makedirs(hls_path, exist_ok=True)
            subprocess.run([
                'ffmpeg', '-i', filepath,
                '-codec: copy', '-start_number', '0',
                '-hls_time', '10', '-hls_list_size', '0',
                '-f', 'hls', os.path.join(hls_path, 'index.m3u8')
            ])

            videos = load_json(VIDEOS_JSON)
            videos.append({
                'id': video_id,
                'title': title,
                'description': description,
                'filename': filename
            })
            save_json(videos, VIDEOS_JSON)

            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/video/<video_id>', methods=['GET', 'POST'])
def video(video_id):
    videos = load_json(VIDEOS_JSON)
    video = next((v for v in videos if v['id'] == video_id), None)
    if not video:
        return "Video not found", 404

    comments = load_json(COMMENTS_JSON)
    video_comments = [c for c in comments if c['video_id'] == video_id]

    if request.method == 'POST':
        username = request.form['username']
        comment_text = request.form['comment']
        comments.append({
            'video_id': video_id,
            'username': username,
            'comment': comment_text
        })
        save_json(comments, COMMENTS_JSON)
        return redirect(url_for('video', video_id=video_id))

    return render_template('video.html', video=video, comments=video_comments)

@app.route('/thumbnails/<filename>')
def thumbnail(filename):
    return send_from_directory(THUMBNAIL_FOLDER, filename)

@app.route('/hls/<video_id>/<filename>')
def hls(video_id, filename):
    return send_from_directory(os.path.join(HLS_FOLDER, video_id), filename)

# Render用：PORT環境変数を使って起動
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
