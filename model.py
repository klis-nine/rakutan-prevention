from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    MetaData,
    select,
)
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin

#追記
from datetime import datetime, timedelta
import threading
import time
from playsound import playsound
import pygame  # pygame をインポート

# グローバル変数としてアラーム関連の情報を初期化
alarm_time = None
alarm_active = False

class User(UserMixin):
    def __init__(self, user_id, email, password):
        self.id = user_id  # flask-login requires `id` attribute
        self.email = email
        self.password = password


class DatabaseManager:
    def __init__(self, database_url="sqlite:///main.db"):
        self.engine = create_engine(database_url)
        self.metadata = MetaData()

        self.accounts = Table(
            "accounts",
            self.metadata,
            Column("user_id", Integer, primary_key=True),
            Column("email", String(255), unique=True),
            Column("password", String(255)),
        )

        self.classes = Table(
            "classes",
            self.metadata,
            Column("class_id", Integer, primary_key=True),
            Column("class_room", String(255)),
            Column("class_name", String(255)),
            Column("class_semester", String(255)),
            Column("class_period", Integer),
            Column("number_of_classes", Integer),
        )

        self.class_registration = Table(
            "class_registrations",
            self.metadata,
            Column(
                "user_id", Integer, ForeignKey("accounts.user_id"), primary_key=True
            ),
            Column(
                "class_id", Integer, ForeignKey("classes.class_id"), primary_key=True
            ),
            Column("absences", Integer),
        )

        self.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        self.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def select_all_accounts(self):
        with self.get_session() as session:
            query = select(self.accounts)
            result = session.execute(query).fetchall()
            return result

    def add_account(self, email, hashed_password):
        with self.get_session() as session:
            query = self.accounts.insert().values(email=email, password=hashed_password)
            session.execute(query)
            session.commit()

    def get_account(self, email):
        with self.get_session() as session:
            query = select(self.accounts).where(self.accounts.c.email == email)
            result = session.execute(query).fetchone()
            if result:
                return User(result.user_id, result.email, result.password)
            return None

    def get_account_by_id(self, user_id):
        with self.get_session() as session:
            query = select(self.accounts).where(self.accounts.c.user_id == user_id)
            result = session.execute(query).fetchone()
            if result:
                return User(result.user_id, result.email, result.password)
            return None

# アラームの処理を記述する関数
def alarm_thread():
    global alarm_time, alarm_active

    def play_alarm_sound():
        print("再生開始")  # デバッグメッセージ
        pygame.mixer.music.load('/music/alarm_sound.mp3')  # 音声ファイルのパスを指定
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(1)
        print("再生終了")  # デバッグメッセージ

    while True:
        if alarm_time and datetime.now() >= alarm_time and alarm_active:
            print("アラームです！")
            
             # スレッドを使って音を鳴らす
            alarm_sound_thread = threading.Thread(target=play_alarm_sound)
            alarm_sound_thread.start()

            # アラームが鳴った後にフラグをリセットする
            alarm_active = False

        time.sleep(1)
