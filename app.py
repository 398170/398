from flask import Flask, render_template, request, redirect, url_for, session
import os, json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションに必要

VIDEO_DB = 'videos.json'

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
