from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    MetaData,
)

engine = create_engine("sqlite:///main.db")

metadata = MetaData()

account = Table(
    "account",
    metadata,
    Column("user_id", Integer, primary_key=True),
    Column("email", String(255), unique=True),
    Column("password", String(255)),
)

classes = Table(
    "classes",
    metadata,
    Column("class_id", Integer, primary_key=True),
    Column("class_room", String(255)),
    Column("class_name", String(255)),
    Column("class_semester", String(255)),
    Column("class_period", Integer),
    Column("number_of_classes", Integer),
)

class_registration = Table(
    "class_registrations",
    metadata,
    Column("user_id", Integer, ForeignKey("account.user_id"), primary_key=True),
    Column("class_id", Integer, ForeignKey("classes.class_id"), primary_key=True),
    Column("absences", Integer),
)

metadata.create_all(engine)
