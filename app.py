import os
import json
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ファイルの読み込みと保存用関数
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# トップページ
@app.route('/')
def index():
    videos = load_data('videos.json')
    return render_template('index.html', videos=videos)

# 動画詳細ページ
@app.route('/video/<int:video_id>')
def watch_video(video_id):
    videos = load_data('videos.json')
    video = videos.get(str(video_id))
    likes = load_data('likes.json')
    video_likes = likes.get(str(video_id), [])
    return render_template('watch.html', video=video, likes=video_likes)

# 動画に「いいね」を追加
@app.route('/like/<int:video_id>', methods=['POST'])
def like_video(video_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    likes = load_data('likes.json')
    video_likes = likes.get(str(video_id), [])
    if username not in video_likes:
        video_likes.append(username)
        likes[str(video_id)] = video_likes
        save_data('likes.json', likes)

    return redirect(url_for('watch_video', video_id=video_id))

# タグ別動画一覧ページ
@app.route('/tag/<tag>')
def tagged_videos(tag):
    videos = load_data('videos.json')
    tagged = [v for v in videos.values() if tag in v.get('tags', [])]
    return render_template('tagged.html', videos=tagged, tag=tag)

# 再生リストに追加
@app.route('/add_to_playlist/<int:video_id>', methods=['POST'])
def add_to_playlist(video_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    playlists = load_data('playlists.json')
    user = session['username']

    if user not in playlists:
        playlists[user] = []

    if video_id not in playlists[user]:
        playlists[user].append(video_id)

    save_data('playlists.json', playlists)
    return redirect(url_for('watch_video', video_id=video_id))

# ユーザーの再生リスト表示
@app.route('/playlist')
def view_playlist():
    if 'username' not in session:
        return redirect(url_for('login'))

    playlists = load_data('playlists.json')
    videos = load_data('videos.json')
    user_videos = [videos[str(v)] for v in playlists.get(session['username'], [])]
    return render_template('playlist.html', videos=user_videos)

# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return render_template('login.html')

# ログアウト
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
