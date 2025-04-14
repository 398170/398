import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os

# Flaskアプリケーションの設定
app = Flask(__name__)
app.secret_key = os.urandom(24)  # セッション管理のための秘密鍵（適切に管理）

# 動画メタデータの保存場所
VIDEO_DB = 'videos.json'

# トップページ
@app.route('/')
def index():
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)
    return render_template('index.html', videos=videos)

# 動画詳細ページ
@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def view_video(video_id):
    with open(VIDEO_DB, 'r') as f:
        videos = json.load(f)

    if video_id < 0 or video_id >= len(videos):
        return "動画が見つかりません", 404

    video = videos[video_id]

    # コメントの読み込み
    comments_file = f'comments_{video_id}.json'
    if os.path.exists(comments_file):
        with open(comments_file, 'r') as f:
            comments = json.load(f)
    else:
        comments = []

    # コメント投稿処理
    if request.method == 'POST':
        comment_text = request.form['comment']
        username = session.get('username', '匿名')

        comments.append({'user': username, 'text': comment_text})

        with open(comments_file, 'w') as f:
            json.dump(comments, f, indent=2)

        return redirect(url_for('view_video', video_id=video_id))

    return render_template('video.html', video=video, comments=comments, video_id=video_id)

# ユーザー登録ページ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # ユーザーの登録処理（実際にはデータベースやファイルに保存）
        return redirect(url_for('index'))
    return render_template('register.html')

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # ユーザー認証処理（実際にはデータベースやファイルで認証）
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('login.html')

# ログアウト処理
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# 動画アップロードページ
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video_file = request.files['video']
        # 動画保存処理、メタデータ保存
        video_id = 0  # 動画IDの生成（実際にはユニークなID生成を行う）
        video_info = {
            'id': video_id,
            'title': title,
            'description': description,
            'filename': video_file.filename
        }

        with open(VIDEO_DB, 'r+') as f:
            videos = json.load(f)
            videos.append(video_info)
            f.seek(0)
            json.dump(videos, f, indent=2)

        # 動画ファイル保存
        video_file.save(os.path.join('static', 'uploads', video_file.filename))

        return redirect(url_for('index'))
    return render_template('upload.html')

if __name__ == "__main__":
    # Renderが提供するPORT環境変数を使ってポートを指定
    port = int(os.environ.get("PORT", 5000))  # デフォルトで5000を使用
    app.run(host="0.0.0.0", port=port)
