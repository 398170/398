from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
VIDEO_JSON = 'videos.json'
COMMENTS_JSON = 'comments.json'
USERS_JSON = 'users.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

def load_json(path, default=[]):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(default, f)
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    videos = load_json(VIDEO_JSON)
    return render_template('index.html', videos=videos)

@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def video(video_id):
    videos = load_json(VIDEO_JSON)
    if video_id < 0 or video_id >= len(videos):
        return "Video not found", 404
    video = videos[video_id]
    comments = load_json(COMMENTS_JSON)
    video_comments = [c for c in comments if c['video_id'] == video_id]
    return render_template('video.html', video=video, video_id=video_id, comments=video_comments)

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
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            videos = load_json(VIDEO_JSON)
            videos.append({'filename': filename, 'title': title, 'description': description})
            save_json(VIDEO_JSON, videos)
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_json(USERS_JSON)
        if any(u['username'] == username for u in users):
            return 'ユーザー名はすでに存在します'
        users.append({'username': username, 'password': password})
        save_json(USERS_JSON, users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_json(USERS_JSON)
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        return 'ログイン失敗'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/comment/<int:video_id>', methods=['POST'])
def comment(video_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    text = request.form['comment']
    comments = load_json(COMMENTS_JSON)
    comments.append({'video_id': video_id, 'user': session['username'], 'text': text})
    save_json(COMMENTS_JSON, comments)
    return redirect(url_for('video', video_id=video_id))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
