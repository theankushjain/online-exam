from app import app, db
from models import Student

def create_user(username, email, password):
    with app.app_context():
        existing_user = Student.query.filter_by(username=username).first()
        if existing_user:
            print(f"User {username} already exists.")
            return

        new_user = Student(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        print(f"User {username} created successfully.")

if __name__ == "__main__":
    # Create some test users
    create_user("student1", "student1@example.com", "password1")
    create_user("student2", "student2@example.com", "password2")
    create_user("student3", "student3@example.com", "password3")

    print("Test users created. You can now log in with these credentials.")