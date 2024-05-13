from flask import Flask

app = Flask(__name__)


@app.route("/")
def return_top():
    return "<p>Hello, World! トップのランディングページです</p>"
@app.route("/user/settings")
def return_user_settings():
    return "<p>Hello, World! ユーザー設定ページです</p>"
@app.route("/user/signup")
def return_user_signup():
    return "<p>Hello, World! アカウント作成ページです</p>"
@app.route("/user/login")
def return_user_login():
    return "<p>Hello, World! ログインページです</p>"
@app.route("/user/main/registration")
def return_user_registration():
    return "<p>Hello, World! 履修登録ページです</p>"
@app.route("/user/main/attendence")
def return_user_attendence():
    return "<p>Hello, World! 出欠席確認です</p>"
@app.route("/user/main/alarm_settings")
def return_user_alarm():
    return "<p>Hello, World! アラーム設定です</p>"
@app.route("/user/main/others-settings")
def return_user_others():
    return "<p>Hello, World! その他の設定ページです</p>"

if __name__ == "__main__":
    app.run()