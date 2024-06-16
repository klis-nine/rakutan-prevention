from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    MetaData,
    select,
    delete,  # ここにdeleteを追加
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

    def add_class(self, class_id, class_room, class_name, class_semester, class_period, number_of_classes):
        try:
            with self.get_session() as session:
                insert_stmt = self.classes.insert().values(
                    class_id=class_id,
                    class_room=class_room,
                    class_name=class_name,
                    class_semester=class_semester,
                    class_period=class_period,
                    number_of_classes=number_of_classes
                )
                session.execute(insert_stmt)
                session.commit()
            return True
        except Exception as e:
            print(f"Error adding class: {e}")
            return False

    def get_class(self, class_id):
        with self.get_session() as session:
            query = select(self.classes).where(self.classes.c.class_id == class_id)
            result = session.execute(query).fetchone()
            if result:
                return dict(result)
            else:
                return None

    def list_class(self, search_words):
        with self.get_session() as session:
            if search_words:
                query = select(self.classes).where(
                    (self.classes.c.class_name.like(f"%{search_words}%")) |
                    (self.classes.c.class_room.like(f"%{search_words}%")) |
                    (self.classes.c.class_semester.like(f"%{search_words}%"))
                )
            else:
                query = select(self.classes)
            
            result = session.execute(query).fetchall()
            return [dict(row) for row in result]
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

# 例えば:
# db_manager = DatabaseManager()
# db_manager.create_tables()
# accounts = db_manager.select_all_accounts()

    def register_user_class(self, user_id, class_id, absences=0):
        with self.get_session() as session:
            session.execute(
                self.class_registration.insert().values(
                    user_id=user_id, class_id=class_id, absences=absences
                )
            )
            session.commit()

    def remove_user_class(self, user_id, class_id):
        with self.get_session() as session:
            session.execute(
                delete(self.class_registration).where(
                    (self.class_registration.c.user_id == user_id) &
                    (self.class_registration.c.class_id == class_id)
                )
            )
            session.commit()

    def list_user_class(self, user_id):
        with self.get_session() as session:
            query = select(self.class_registration).where(
                self.class_registration.c.user_id == user_id
            )
            result = session.execute(query).fetchall()
            return result
        
#実装確認     
# インスタンスを作成してからメソッドを呼び出す
#db_manager = DatabaseManager()
#db_manager.register_user_class(user_id=1, class_id=101)
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


