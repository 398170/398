from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# 動画保存用フォルダ設定
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# アップロード先フォルダを作成（なければ）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# トップページ（アップロードフォームと動画一覧）
@app.route('/')
def index():
    videos = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', videos=videos)

# アップロード処理
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['video']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
    return redirect(url_for('index'))

# 動画再生ページ
@app.route('/watch/<filename>')
def watch(filename):
    return render_template('watch.html', filename=filename)

# Railway対応（ポートを環境変数から取得）
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
