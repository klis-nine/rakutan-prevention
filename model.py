from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    MetaData,
    select,
    delete,
    update,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin
import logging

Base = declarative_base()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class User(Base, UserMixin):
    __tablename__ = "accounts"
    user_id = Column(String(255), primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    phone_number = Column(String(255))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __init__(self, user_id, name=None, email=None, phone_number=None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone_number = phone_number


class Class(Base):
    __tablename__ = "classes"
    class_id = Column(String(255), primary_key=True)
    class_room = Column(String(255))
    class_name = Column(String(255))
    class_semester = Column(String(255))
    class_period = Column(String(255))
    number_of_classes = Column(Integer)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ClassRegistration(Base):
    __tablename__ = "class_registrations"
    user_id = Column(Integer, ForeignKey("accounts.user_id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.class_id"), primary_key=True)
    absences = Column(Integer)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class DatabaseManager:
    def __init__(self, database_url="sqlite:///main.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def select_all_accounts(self):
        with self.get_session() as session:
            query = select(User)
            result = session.execute(query).scalars().all()
            return [user.to_dict() for user in result]

    def add_class(
        self,
        class_id,
        class_room,
        class_name,
        class_semester,
        class_period,
        number_of_classes,
    ):
        with self.get_session() as session:
            try:
                new_class = Class(
                    class_id=class_id,
                    class_room=class_room,
                    class_name=class_name,
                    class_semester=class_semester,
                    class_period=class_period,
                    number_of_classes=number_of_classes,
                )
                session.add(new_class)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error adding class: {e}")
                return False

    def get_class(self, class_id):
        with self.get_session() as session:
            result = session.get(Class, class_id)
            return result.to_dict() if result else None

    def list_class(self, search_words):
        with self.get_session() as session:
            query = select(Class)
            if search_words:
                query = query.where(
                    (Class.class_name.like(f"%{search_words}%"))
                    | (Class.class_room.like(f"%{search_words}%"))
                    | (Class.class_semester.like(f"%{search_words}%"))
                )
            result = session.execute(query).scalars().all()
            return [cls.to_dict() for cls in result]

    def add_account(self, user_id, name=None, email=None, phone_number=None):
        with self.get_session() as session:
            try:
                new_user = User(
                    user_id=user_id,
                    name=name,
                    email=email,
                    phone_number=phone_number,
                )
                session.add(new_user)
                session.commit()
                return True
            except IntegrityError as e:
                session.rollback()
                logger.error(f"Error adding account: {e}")
                return False

    def get_account(self, user_id):
        with self.get_session() as session:
            result = session.get(User, user_id)
            print(result)
            return result.to_dict() if result else None

    def register_user_class(self, user_id, class_id, absences=0):
        with self.get_session() as session:
            try:
                result = session.get(
                    ClassRegistration, {"user_id": user_id, "class_id": class_id}
                )
                if result:
                    logger.info("User is already registered for this class.")
                    return False
                new_registration = ClassRegistration(
                    user_id=user_id, class_id=class_id, absences=absences
                )
                session.add(new_registration)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error registering user to class: {e}")
                return False

    def update_user_absences(self, user_id, class_id, absences):
        with self.get_session() as session:
            try:
                query = (
                    update(ClassRegistration)
                    .where(
                        (ClassRegistration.user_id == user_id)
                        & (ClassRegistration.class_id == class_id)
                    )
                    .values(absences=absences)
                )
                session.execute(query)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error updating user absences: {e}")
                return False

    def remove_user_class(self, user_id, class_id):
        with self.get_session() as session:
            try:
                query = delete(ClassRegistration).where(
                    (ClassRegistration.user_id == user_id)
                    & (ClassRegistration.class_id == class_id)
                )
                session.execute(query)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error removing user from class: {e}")
                return False

    def list_user_class(self, user_id):
        with self.get_session() as session:
            query = select(ClassRegistration).where(
                ClassRegistration.user_id == user_id
            )
            result = session.execute(query).scalars().all()
            return [registration.to_dict() for registration in result]

    def get_account_by_id(self, user_id):
        with self.get_session() as session:
            result = session.get(User, user_id)
            return result if result else None
