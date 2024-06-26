from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import logging
import os
import jwt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import Base, User, Class, ClassRegistration, DatabaseManager
import dotenv
from flask_cors import CORS
import jwt
from jwt.algorithms import RSAAlgorithm
import requests
import json
from notifier import call_number, send_sms

dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///main.db"
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

db = SQLAlchemy(app)
database_manager = DatabaseManager()

# ログ周り
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auth0周り
AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]
API_AUDIENCE = os.environ["API_AUDIENCE"]
AUTH0_PUBLIC_KEY = os.environ["AUTH0_PUBLIC_KEY"]


# 分離しておく、のほうが管理者権限周りとか作りやすそうなので
def permissionCheck(request_user_id, user_id):
    # 管理者でない場合は、自分のアカウントのみ操作可能
    if request_user_id != user_id and request_user_id != "admin":
        return False
    return True


def get_token_auth_header():
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise Exception("Authorization header is expected")

    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise Exception("Authorization header must start with 'Bearer'")
    elif len(parts) == 1:
        raise Exception("Token not found")
    elif len(parts) > 2:
        raise Exception("Authorization header must be Bearer token")

    token = parts[1]
    return token


JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
JWKS = requests.get(JWKS_URL).json()


def get_token_auth_header():
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise Exception("Authorization header is expected")

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise Exception("Authorization header must start with Bearer")
    elif len(parts) == 1:
        raise Exception("Token not found")
    elif len(parts) > 2:
        raise Exception("Authorization header must be Bearer token")

    token = parts[1]
    return token


def get_rsa_key(kid):
    for key in JWKS["keys"]:
        if key["kid"] == kid:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            print(rsa_key)
            return RSAAlgorithm.from_jwk(json.dumps(rsa_key))
    return None


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = get_rsa_key(unverified_header["kid"])
        if rsa_key is None:
            return jsonify({"message": "Unable to find appropriate key"}), 401

        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        if not database_manager.get_account(payload["sub"]):
            print(payload)
            database_manager.add_account(payload["sub"])

        return f(payload, *args, **kwargs)

    return decorated


@app.route("/api/accounts", methods=["POST"])
@requires_auth
def create_account(payload):
    data = request.get_json()
    user_id = payload["sub"]
    phone_number = data.get("phone_number") or None

    if database_manager.get_account(user_id):
        return jsonify({"message": "Account already exists"}), 400

    success = database_manager.add_account(user_id, phone_number=phone_number)
    if success:
        return jsonify({"message": "Account created successfully"}), 201
    else:
        return jsonify({"message": "Failed to create account"}), 500


@app.route("/api/accounts/<user_id>", methods=["GET"])
@requires_auth
def get_account(payload, user_id):
    current_user_id = payload["sub"]
    if permissionCheck(current_user_id, user_id) == False:
        return jsonify({"message": "You are not allowed to view this account"}), 403

    account = database_manager.get_account(user_id)
    if account:
        return jsonify(account), 200
    else:
        return jsonify({"message": "Account not found"}), 404


@app.route("/api/accounts/<user_id>", methods=["PUT"])
@requires_auth
def update_account(payload, user_id):
    current_user_id = payload["sub"]
    if permissionCheck(current_user_id, user_id) == False:
        return jsonify({"message": "You are not allowed to update this account"}), 403
    account = database_manager.get_account(user_id)
    if not account:
        return jsonify({"message": "Account not found"}), 404
    data = request.get_json()
    phone_number = data.get("phone_number")
    account["phone_number"] = phone_number
    session = database_manager.get_session()
    user_columns = {c.key for c in User.__table__.columns}
    filtered_account = {k: v for k, v in account.items() if k in user_columns}
    session.query(User).filter(User.user_id == user_id).update(
        filtered_account, synchronize_session=False
    )
    print("FFF")
    session.commit()

    return jsonify({"message": "Account updated successfully"}), 200


@app.route("/api/classes", methods=["GET"])
@requires_auth
def list_classes(payload):
    search_words = request.args.get("search", "")
    classes = database_manager.list_class(search_words)
    return jsonify(classes), 200


@app.route("/api/classes", methods=["POST"])
@requires_auth
def create_class(payload):
    data = request.get_json()
    class_id = data["class_id"]
    class_room = data["class_room"]
    class_name = data["class_name"]
    class_semester = data["class_semester"]
    class_period = data["class_period"]
    number_of_classes = data["number_of_classes"]

    success = database_manager.add_class(
        class_id,
        class_room,
        class_name,
        class_semester,
        class_period,
        number_of_classes,
    )
    if success:
        return jsonify({"message": "Class created successfully"}), 201
    else:
        return jsonify({"message": "Failed to create class"}), 500


@app.route("/api/classes/<class_id>", methods=["GET"])
@requires_auth
def get_class(payload, class_id):
    cls = database_manager.get_class(class_id)
    if cls:
        return jsonify(cls), 200
    else:
        return jsonify({"message": "Class not found"}), 404


@app.route("/api/classes/<class_id>", methods=["PUT"])
@requires_auth
def update_class(payload, class_id):
    data = request.get_json()
    class_room = data.get("class_room")
    class_name = data.get("class_name")
    class_semester = data.get("class_semester")
    class_period = data.get("class_period")
    number_of_classes = data.get("number_of_classes")

    updated_data = {
        "class_room": class_room,
        "class_name": class_name,
        "class_semester": class_semester,
        "class_period": class_period,
        "number_of_classes": number_of_classes,
    }

    session = database_manager.get_session()
    class_columns = {c.key for c in Class.__table__.columns}
    filtered_data = {k: v for k, v in updated_data.items() if k in class_columns}

    session.query(Class).filter(Class.class_id == class_id).update(filtered_data)
    session.commit()

    return jsonify({"message": "Class updated successfully"}), 200


@app.route("/api/classes/<class_id>", methods=["DELETE"])
@requires_auth
def delete_class(payload, class_id):
    current_user_id = payload["sub"]
    if permissionCheck(current_user_id, "") == False:
        return jsonify({"message": "You are not allowed to update this class"}), 403
    cls = database_manager.get_class(class_id)
    if not cls:
        return jsonify({"message": "Class not found"}), 404

    session = database_manager.get_session()
    session.query(Class).filter(Class.class_id == class_id).delete()
    session.commit()

    return jsonify({"message": "Class deleted successfully"}), 204


@app.route("/api/class_registrations", methods=["GET"])
@requires_auth
def list_class_registrations(payload):
    user_id = payload["sub"]
    registrations = database_manager.list_user_class(user_id)
    return jsonify(registrations), 200


@app.route("/api/class_registrations", methods=["POST"])
@requires_auth
def register_class(payload):
    data = request.get_json()
    user_id = payload["sub"]
    class_id = data["class_id"]
    absences = data.get("absences", 0)
    success = database_manager.register_user_class(user_id, class_id, absences)
    if success:
        return jsonify({"message": "User registered to class successfully"}), 201
    else:
        return jsonify({"message": "User is already registered to this class"}), 400


@app.route("/api/class_registrations/<user_id>/<class_id>", methods=["PUT"])
@requires_auth
def update_absences(payload, user_id, class_id):
    current_user_id = payload["sub"]
    if permissionCheck(current_user_id, user_id) == False:
        return (
            jsonify(
                {"message": "You are not allowed to update absences for this user"}
            ),
            403,
        )

    data = request.get_json()
    absences = data.get("absences")
    if absences is None:
        return jsonify({"message": "Absences is required"}), 400

    success = database_manager.update_user_absences(user_id, class_id, absences)
    if success:
        return jsonify({"message": "Absences updated successfully"}), 200
    else:
        return jsonify({"message": "Failed to update absences"}), 500


@app.route("/api/class_registrations/<user_id>/<class_id>", methods=["DELETE"])
@requires_auth
def unregister_class(payload, user_id, class_id):
    current_user_id = payload["sub"]
    if permissionCheck(current_user_id, user_id) == False:
        return (
            jsonify(
                {"message": "You are not allowed to unregister this user from class"}
            ),
            403,
        )

    success = database_manager.remove_user_class(user_id, class_id)
    if success:
        return jsonify({"message": "User unregistered from class successfully"}), 204
    else:
        return jsonify({"message": "Failed to unregister user from class"}), 500


@app.route("/api/callme", methods=["GET"])
@requires_auth
def callme(payload):
    user_id = payload["sub"]
    account = database_manager.get_account(user_id)
    phone_number = account["phone_number"]
    print(phone_number)
    # Convert the local phone number to phone number with suffix
    phone_number = "+81" + phone_number[1:]
    result = call_number(
        phone_number, "http://storage.googleapis.com/rakutanprev/qecycncrci.mp3"
    )
    if result:
        return jsonify(account), 200
    else:
        return jsonify({"message": "Failed to call"}), 500


@app.route("/api/sendsms", methods=["GET"])
@requires_auth
def callmesms(payload):
    user_id = payload["sub"]
    account = database_manager.get_account(user_id)
    phone_number = account["phone_number"]
    print(phone_number)
    # Convert the local phone number to phone number with suffix
    phone_number = "+81" + phone_number[1:]
    result = send_sms(phone_number, "電話番号が登録されました!")

    if result:
        return jsonify(account), 200
    else:
        return jsonify({"message": "Failed to call"}), 500


if __name__ == "__main__":
    app.run(debug=True)
