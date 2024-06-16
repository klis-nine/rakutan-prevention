from flask import Flask, render_template, request, redirect
from model import DatabaseManager, User, alarm_thread
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import hashlib
#追記
from datetime import datetime, timedelta
import threading
import time


app = Flask(__name__)
app.secret_key = "secret"

login_manager = LoginManager()
login_manager.init_app(app)

# アラーム用のグローバル変数
alarm_time = None
alarm_active = False

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
    return render_template("prev-main.html", user_email=current_user.email)

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
    #return "<p>Hello, World! 履修登録ページです</p>"
    return render_template("class-situation.html")

@app.route("/user/main/attendence")
@login_required
def return_user_attendence():
    #return "<p>Hello, World! 出欠席確認です</p>"
    return render_template("attend-prev.html")

@app.route("/user/main/alarm_settings")
@login_required
def return_user_alarm():
    #return "<p>Hello, World! アラーム設定です</p>"
    return render_template("alarm-setting.html")

@app.route("/user/main/others-settings")
@login_required
def return_user_others():
    #return "<p>Hello, World! その他の設定ページです</p>"
    return render_template("mypage-prev.html")

@app.route("/user/main/others-settings/forgetpass")
@login_required
def return_user_others_pass():
    #return "<p>Hello, World! その他の設定ページです</p>"
    return render_template("pass-forget1.html")

#追記
# アラーム設定用のエンドポイント
@app.route('/set_alarm', methods=['POST'])
def set_alarm():
    global alarm_time, alarm_active

    time_str = request.form['timeInput']
    alarm_time = datetime.strptime(time_str, "%H:%M").time()

    # 現在の日付とセットした時間を組み合わせて datetime オブジェクトを作成
    now = datetime.now()
    alarm_time = datetime.combine(now.date(), alarm_time)

    # アラームをアクティブにする
    alarm_active = True

    return "アラームが設定されました！"

if __name__ == '__main__':
    # バックグラウンドでアラームを監視するスレッドを起動
    alarm_checker = threading.Thread(target=alarm_thread)
    alarm_checker.start()

    # Flaskアプリケーションを起動
    app.run(debug=True)