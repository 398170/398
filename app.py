from flask import Flask, render_template, request, redirect, url_for
import os, json
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
VIDEO_DB = 'videos.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# データベースがなければ初期化
if not os.path.exists(VIDEO_DB):
    with open(VIDEO_DB, 'w') as f:
        json.dump([], f)

@app.route('/')
def index():
    # 動画リストを読み込み
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

            # 動画情報を保存
            with open(VIDEO_DB, 'r') as f:
                videos = json.load(f)
            videos.append({
                'title': title,
                'description': description,
                'filename': filename
            })
            with open(VIDEO_DB, 'w') as f:
                json.dump(videos, f, indent=2)

            return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/watch/<int:video_id>')
def watch(video_id):
    # 動画情報を読み込み
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    # 指定されたIDの動画を取得
    video = videos[video_id]
    return render_template('watch.html', video=video)

if __name__ == '__main__':
    app.run(debug=True)
