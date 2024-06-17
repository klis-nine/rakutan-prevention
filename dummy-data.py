from model import Base, User, Class, ClassRegistration, DatabaseManager

database_manager = DatabaseManager()

database_manager.add_class(
    class_id="GE10001",
    class_room="A101",
    class_name="知識概論",
    class_semester="SA,SB",
    class_period="1,2",
    number_of_classes=15,
)

database_manager.register_user_class(
    user_id="google-oauth2|105038472575077144999", class_id="GE10001", absences=0
)
