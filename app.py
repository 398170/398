import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# アップロード先のディレクトリ
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MBの制限

# 許可するファイル拡張子
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# ファイルの拡張子が許可されているか確認
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # 動画データの読み込み（仮にjsonファイルから読み込む場合）
    try:
        with open('videos.json', 'r') as f:
            videos = json.load(f)
    except FileNotFoundError:
        videos = []
    
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if video_file and allowed_file(video_file.filename):
        # セキュアなファイル名を取得
        filename = secure_filename(video_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # ファイル保存
        video_file.save(filepath)
        
        # 動画メタデータの保存（仮）
        title = request.form.get('title')
        description = request.form.get('description')
        
        video_data = {
            'title': title,
            'description': description,
            'filename': filename
        }
        
        # 動画メタデータをJSONに保存
        try:
            with open('videos.json', 'r') as f:
                videos = json.load(f)
        except FileNotFoundError:
            videos = []
        
        videos.append(video_data)
        
        with open('videos.json', 'w') as f:
            json.dump(videos, f)
        
        flash('Video successfully uploaded')
        return redirect(url_for('index'))
    else:
        flash('Invalid file format')
        return redirect(request.url)

@app.errorhandler(500)
def internal_error(error):
    return "Internal Server Error. Please try again later.", 500

if __name__ == "__main__":
    # 静的ファイルの保存先ディレクトリを作成
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # アプリケーションを起動（デバッグモード有効）
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
