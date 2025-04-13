from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# アップロード用のフォルダを指定
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov'}

# ファイル拡張子のチェック
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 動画アップロードページ
@app.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'ファイルがありません'
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            return redirect(url_for('video_page', filename=file.filename))
    return render_template('upload.html')

# 動画再生ページ
@app.route('/video/<filename>')
def video_page(filename):
    return render_template('video.html', filename=filename)

if __name__ == '__main__':
    app.run(debug=True)
