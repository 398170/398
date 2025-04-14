from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # セッションを使うための秘密鍵

# 動画データを保存するファイルパス
VIDEO_JSON_FILE = 'videos.json'

# ユーザーのログイン状態を管理するためのセッション（仮）
logged_in_user = None

# 動画データを読み込む関数
def load_videos():
    if os.path.exists(VIDEO_JSON_FILE):
        with open(VIDEO_JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# トップページ（動画一覧）表示
@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

# ログインページ表示と処理
@app.route('/login', methods=['GET', 'POST'])
def login():
    global logged_in_user
    if request.method == 'POST':
        # フォームから送信されたユーザー名とパスワードを取得
        username = request.form['username']
        password = request.form['password']
        
        # 仮の認証処理（ここで実際の認証ロジックを実装）
        if username == 'admin' and password == 'password':
            logged_in_user = username
            flash('ログイン成功！')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名かパスワードが間違っています。')
    
    return render_template('login.html')

# ログアウト処理
@app.route('/logout')
def logout():
    global logged_in_user
    logged_in_user = None
    flash('ログアウトしました。')
    return redirect(url_for('index'))

# 動画アップロードページ（仮）
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # 動画ファイルのアップロード処理（仮）
        title = request.form['title']
        description = request.form['description']
        
        # 動画情報を保存（仮）
        video_data = {
            'title': title,
            'description': description,
            'file': 'sample_video.mp4',  # 実際にはファイルアップロード処理が必要
        }
        
        # 動画情報をJSONファイルに追加
        videos = load_videos()
        videos.append(video_data)
        with open(VIDEO_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=4)
        
        flash('動画がアップロードされました！')
        return redirect(url_for('index'))
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
