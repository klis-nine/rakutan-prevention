from flask import Flask, render_template, request, redirect
from model import DatabaseManager, User
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import hashlib

app = Flask(__name__)
app.secret_key = "secret"

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db = DatabaseManager()
    return db.get_account_by_id(user_id)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/")
def return_top():
    if current_user.is_authenticated:
        return redirect("/user/main")
    return render_template("prev-first.html")

@app.route("/user/main")
@login_required
def return_user_main():
    return "<p>Hello, World! ユーザーメインページです</p><p>あなたのユーザーIDは{}です</p>".format(
        current_user.id
    )

@app.route("/user/settings")
@login_required
def return_user_settings():
    return "<p>Hello, World! ユーザー設定ページです</p>"


@app.route("/user/signup", methods=["GET", "POST"])
def return_user_signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        print(
            "Creating account with email: {} and password: {}".format(email, password)
        )
        hashed_password = hash_password(password)
        db = DatabaseManager()
        if db.get_account(email):
            print("該当するアカウントは既に存在しています")
            # TODO: このprintをいい感じにクライアントに反映させる
            return redirect("/user/signup")
        try:
            db.add_account(email, hashed_password)
            print("Account created")
            return redirect("/user/login")
        except Exception as e:
            print(e)
            return redirect("/user/signup")
    return render_template("prev-create.html")


@app.route("/user/login", methods=["GET", "POST"])
def return_user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        print("Logging in with email: {} and password: {}".format(email, password))
        db = DatabaseManager()
        user = db.get_account(email)
        if user and user.password == hash_password(password):
            login_user(user)
            print("Logged in")
            return redirect("/user/main")
        else:
            return redirect("/user/login")
    return render_template("prev-login.html")


@app.route("/user/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/user/main/registration")
@login_required
def return_user_registration():
    return "<p>Hello, World! 履修登録ページです</p>"


@app.route("/user/main/attendence")
@login_required
def return_user_attendence():
    return "<p>Hello, World! 出欠席確認です</p>"


@app.route("/user/main/alarm_settings")
@login_required
def return_user_alarm():
    return "<p>Hello, World! アラーム設定です</p>"


@app.route("/user/main/others-settings")
@login_required
def return_user_others():
    return "<p>Hello, World! その他の設定ページです</p>"


if __name__ == "__main__":
   app.run()