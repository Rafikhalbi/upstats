from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
    session,
    flash,
)
from db import UserDb
import re
from flask_session import Session
import random
import string
import os
import shutil
from werkzeug.utils import secure_filename

web = Flask(__name__)
web.config["SESSION_TYPE"] = "filesystem"
Session(web)


def check_input(data: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", data)
    return clean


def generate_random_id(length=8):
    random_id = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
    return random_id


@web.route("/register", methods=["GET", "POST"])
def register():
    error = None
    succ = None

    if "username" in session:
        return redirect("/")

    if request.method == "POST":
        username = check_input(request.form["username"])
        password = check_input(request.form["password"])
        name = check_input(request.form["name"])

        db = UserDb("databases.db")
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "Username already in use."
        else:
            db.add_user(username, password, name)
            db.close()
            succ = "Registrasi success!"

    return render_template("registrasi/index.html", error=error, succ=succ)


@web.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect("/")

    error = None
    succ = None

    if request.method == "POST":
        username = check_input(request.form["username"])
        password = check_input(request.form["password"])

        db = UserDb("databases.db")
        is_valid_user = db.verify_credentials(username, password)

        if is_valid_user:
            user_info = db.get_user_info(username)
            if user_info:
                response = make_response(redirect("/"))
                session["username"] = username
                db.close()
                return response
        else:
            error = "username/password wrong!"

    return render_template("login/index.html", error=error, succ=succ)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "mp4", "avi", "mkv", "mov"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@web.route("/post", methods=["GET", "POST"])
def create_post():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session.get("username")
    error = None
    succ = None

    db = UserDb("databases.db")

    if request.method == "POST":
        title = request.form["title"]
        uploaded_file = request.files["file"]

        if uploaded_file and allowed_file(uploaded_file.filename):
            secure_file_name = secure_filename(
                generate_random_id() + uploaded_file.filename
            )
            file_path = os.path.join("static/file", secure_file_name)
            uploaded_file.save(file_path)

        else:
            secure_file_name = None

        db.add_post(
            title=title,
            content=secure_file_name,
            user_id=generate_random_id(),
            username=username,
        )
        db.close()
        succ = "Succes create post"

    return render_template("post/index.html", succ=succ)


@web.route("/like", methods=["GET", "POST"])
def like():
    if request.method == "POST":
        db = UserDb("databases.db")
        post_id = request.form["post_id"]
        username = session.get("username")
        user_id = db.get_user_id_by_username(username)

        if user_id:
            has_liked = db.check_if_user_liked_post(user_id, post_id)

            if not has_liked:
                db.add_like(user_id, post_id)

            db.close()
            return redirect("/")


@web.route("/")
def home():
    login_view = False
    if "username" not in session:
        login_view = True

    db = UserDb("databases.db")
    all_posts = db.get_all_posts_sorted_by_newest()
    db.close()
    return render_template(
        "home/index.html", all_posts=all_posts, login_view=login_view
    )


@web.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@web.route("/view/<post_id>")
def post_preview(post_id):
    db = UserDb("databases.db")
    post = db.get_post_by_id(post_id)
    return render_template("view/index.html", post=post)


if __name__ == "__main__":
    web.run(debug=True)
