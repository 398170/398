from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# フォルダがなければ作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    videos = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['video']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
    return redirect(url_for('index'))

@app.route('/watch/<filename>')
def watch(filename):
    return render_template('watch.html', filename=filename)

if __name__ == '__main__':
    app.run(debug=True)
