from flask import Flask, render_template, request, redirect, url_for, jsonify
from model import DatabaseManager, User
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import hashlib
import pandas as pd 
import json 
from your_module import add_class, get_class

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
    return "<p>Hello, World! トップのランディングページです</p> サインアップ→<a href='/user/signup'>こちら</a> ログイン→<a href='/user/login'>こちら</a>"


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
            if db.add_account(email, hashed_password):
                print("Account created")
                return redirect(url_for('return_user_login'))
            else:
                print("Account creation failed")
                return redirect(url_for('return_user_signup'))
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

@app.route("/user/main/register_class/confirm", methods=["GET", "POST"])
@login_required
def return_class_registration_confirm():
    class_id = request.args.get("class_id")
    db = DatabaseManager()

    print(f"クラスID: {class_id}") #クエリパラメータのデバッグ用ログ

    if request.method == "POST":
        class_id = request.form.get("class_id")
        print(f"クラスID (POST): {class_id}") #デバッグ用ログ 

        if class_id:    
            if db.register_user_class(current_user.id, class_id):
                return redirect(url_for('return_user_main'))
            else: 
                print("クラス登録に失敗しました")  # デバッグ用ログ
                return "クラス登録に失敗しました。"
        
        else:
            print("クラスIDが指定されていません (POST)")  # デバッグ用ログ
            return "クラスIDが指定されていません。"

    if class_id:    
        class_info = db.get_class("class_id")
        if class_info:
            return render_template("search-confirm.html", class_info=class_info)
        else:
            print("指定されたクラスが見つかりませんでした")  # デバッグ用ログ
            return "指定されたクラスが見つかりませんでした。"
    else:
        print("クラスIDが指定されていません (GET)")  # デバッグ用ログ
        return "クラスIDが指定されていません。"
    
# 追加: 授業情報のインポートエンドポイント
@app.route("/import_classes", methods=["GET"])
def import_classes():
    try:
        # 正しい列インデックスを指定
        df = pd.read_csv("kdb.csv", skiprows=3, header=None, usecols=[0, 2, 3])
        df.dropna(subset=[0], inplace=True)
        df = df[df[0] != "科目番号"].dropna(thresh=3)
        df.fillna("", inplace=True)

        # 授業IDと授業名を分離
        df['class_id'] = df[0].apply(lambda x: ''.join(filter(str.isdigit, str(x))))
        df['class_name'] = df[0].apply(lambda x: ''.join(filter(lambda c: not c.isdigit(), str(x))).strip())

        for class_info in df.values.tolist():
            add_class({
                "class_id": class_info[3],  # class_id列
                "class_name": class_info[4],  # class_name列
                "class_time": class_info[1],  # 授業時間
                "class_location": class_info[2],  # 教室
            })

        return jsonify({"message": "授業情報のインポートが完了しました。"}), 200
    except Exception as e:
        return jsonify({"message": "エラーが発生しました。", "error": str(e)}), 500


# 追加: 検索フォームの処理
@app.route("/search", methods=["GET", "POST"])
@login_required
def search_classes():
    keyword = request.form.get("keyword")
    db = DatabaseManager()
    if keyword:
        classes = db.search_classes(keyword)
    else:
        classes = []
    return render_template("class-situation.html", classes=classes)

if __name__ == "__main__":
    app.run(debug=True)
