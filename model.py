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
