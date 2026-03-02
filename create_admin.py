from app import create_app
from app.extensions import db
from app.models.user import AdminUser
from app.services.security import hash_password

app = create_app()

with app.app_context():
    if AdminUser.query.first():
        print("Admin already exists. Aborting.")
        exit(0)

    username = input("Admin username: ")
    password = input("Admin password: ")

    admin = AdminUser(
        username=username,
        password_hash=hash_password(password)
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin user created successfully.")
