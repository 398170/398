from flask import Flask, render_template, request, redirect, url_for, session
import json, os
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "secret"

VIDEO_FILE = "data/videos.json"
COMMENT_FILE = "data/comments.json"
USER_FILE = "data/users.json"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

def load_data(file):
    if not os.path.exists(file):
        return []
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    videos = load_data(VIDEO_FILE)
    return render_template("index.html", videos=videos)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form["title"]
        url = request.form["url"]
        video = {
            "id": str(uuid4()),
            "title": title,
            "url": url,
            "likes": 0
        }
        videos = load_data(VIDEO_FILE)
        videos.append(video)
        save_data(VIDEO_FILE, videos)
        return redirect(url_for("index"))
    return render_template("upload.html")

@app.route("/watch/<video_id>", methods=["GET", "POST"])
def watch(video_id):
    videos = load_data(VIDEO_FILE)
    video = next((v for v in videos if v["id"] == video_id), None)
    if not video:
        return "動画が見つかりません", 404

    comments = load_data(COMMENT_FILE)
    video_comments = [c for c in comments if c["video_id"] == video_id]

    if request.method == "POST":
        comment = {
            "video_id": video_id,
            "username": session.get("username", "匿名"),
            "text": request.form["comment"]
        }
        comments.append(comment)
        save_data(COMMENT_FILE, comments)
        return redirect(url_for("watch", video_id=video_id))

    return render_template("watch.html", video=video, comments=video_comments)

@app.route("/like/<video_id>")
def like(video_id):
    videos = load_data(VIDEO_FILE)
    for v in videos:
        if v["id"] == video_id:
            v["likes"] += 1
            break
    save_data(VIDEO_FILE, videos)
    return redirect(url_for("watch", video_id=video_id))

@app.route("/delete/<video_id>")
def delete(video_id):
    if not session.get("admin"):
        return "権限がありません", 403
    videos = load_data(VIDEO_FILE)
    videos = [v for v in videos if v["id"] != video_id]
    save_data(VIDEO_FILE, videos)

    comments = load_data(COMMENT_FILE)
    comments = [c for c in comments if c["video_id"] != video_id]
    save_data(COMMENT_FILE, comments)
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_data(USER_FILE)
        if any(u["username"] == username for u in users):
            return "すでに登録されています"
        users.append({"username": username, "password": password})
        save_data(USER_FILE, users)
        session["username"] = username
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_data(USER_FILE)
        if any(u["username"] == username and u["password"] == password for u in users):
            session["username"] = username
            return redirect(url_for("index"))
        return "ログイン失敗"
    return render_template("user_login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            session["username"] = username
            return redirect(url_for("index"))
        return "ログイン失敗"
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
