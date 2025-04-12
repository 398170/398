from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

VIDEOS_FILE = 'videos.json'

# JSONファイル初期化（なければ作成）
if not os.path.exists(VIDEOS_FILE):
    with open(VIDEOS_FILE, 'w') as f:
        json.dump([], f)

@app.route('/')
def index():
    with open(VIDEOS_FILE, 'r') as f:
        videos = json.load(f)
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['POST'])
def upload():
    title = request.form['title']
    url = request.form['url']
    
    # サポート対象URLかどうか確認
    if any(s in url for s in ['youtube.com', 'youtu.be', 'nicovideo.jp', 'web.archive.org']):
        new_video = {'title': title, 'url': url}
        with open(VIDEOS_FILE, 'r+') as f:
            videos = json.load(f)
            videos.append(new_video)
            f.seek(0)
            json.dump(videos, f, indent=2)
        return redirect(url_for('index'))
    else:
        return 'このURLはサポートされていません。'

@app.route('/watch/<int:video_id>')
def watch(video_id):
    with open(VIDEOS_FILE, 'r') as f:
        videos = json.load(f)
    if 0 <= video_id < len(videos):
        video = videos[video_id]
        return render_template('watch.html', video=video)
    else:
        return '動画が見つかりません。'
