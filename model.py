from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    MetaData,
    select,
    update
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
    
    def get_absences(self,user_id, class_id):
        with self.get_session() as session:   
            query = select([self.class_registration.c.absences]).where(
            (self.class_registration.c.user_id == user_id) &
            (self.class_registration.c.class_id == class_id)
            )
            result = session.execute(query).fetchone()
            if result:
                 return result["absences"]
            else:
                 return None
    
    def change_absences(self, user_id, class_id, absences_count):
        with self.get_session() as session:  
            query = select([self.class_registration]).where(
                    (self.class_registration.c.user_id == user_id) &
                    (self.class_registration.c.class_id == class_id)
                )
            result = session.execute(query).fetchone()

            if result:
                stmt = update(self.class_registration).where(
                  (self.class_registration.c.user_id == user_id) &
                  (self.class_registration.c.class_id == class_id)
                ).values(absences=absences_count)
                session.execute(stmt)
                session.commit()
                return f"Absences for user_id {user_id} in class_id {class_id} updated to {absences_count}."
            else:
                return f"No registration found for user_id {user_id} in class_id {class_id}."

    def add_absences(self, user_id, class_id):
        with self.get_session() as session:  
            current_absences = self.get_absences(user_id, class_id)
            if current_absences is not None:
                new_absences_count = current_absences + 1
                return self.change_absences(user_id, class_id, new_absences_count)
            else:
                return f"No registration found for user_id {user_id} in class_id {class_id}."