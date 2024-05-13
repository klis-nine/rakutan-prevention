from flask import Flask

app = Flask(__name__)

@app.route("/")
def return_top():
    return "<p>Hello, World! トップのランディングページです</p>"
@app.route("/user/settings")
def return_user_settings():
    return "<p>Hello, World! ユーザー設定ページです</p>"