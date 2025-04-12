from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

VIDEO_FILE = "data/videos.json"
USER_FILE = "data/users.json"
COMMENT_FILE = "data/comments.json"

def load_data(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    videos = load_data(VIDEO_FILE)
    return render_template("index.html", videos=videos)

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
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_data(USER_FILE)
        if any(u["username"] == username and u["password"] == password for u in users):
            session["username"] = username
            return redirect(url_for("index"))
        return "ログイン失敗"
    return render_template("user_login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
