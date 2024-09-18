from app import app, db
from models import Student, Question
from elo import get_initial_elo_rating

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()

        # Add a test student
        if not Student.query.filter_by(username='test_student').first():
            test_student = Student(username='test_student', email='test@example.com')
            test_student.set_password('password123')
            db.session.add(test_student)

        # Add some test questions
        if Question.query.count() == 0:
            questions = [
                {
                    'course': 'Math',
                    'topic': 'Algebra',
                    'statement': 'What is 2 + 2?',
                    'option_1': '3',
                    'option_2': '4',
                    'option_3': '5',
                    'option_4': '6',
                    'correct_option': 2,
                    'blooms_taxonomy_level': 1
                },
                {
                    'course': 'Science',
                    'topic': 'Biology',
                    'statement': 'What is the powerhouse of the cell?',
                    'option_1': 'Nucleus',
                    'option_2': 'Mitochondria',
                    'option_3': 'Endoplasmic Reticulum',
                    'option_4': 'Golgi Apparatus',
                    'correct_option': 2,
                    'blooms_taxonomy_level': 2
                },
                # Add more questions as needed
            ]

            for q in questions:
                question = Question(
                    course=q['course'],
                    topic=q['topic'],
                    statement=q['statement'],
                    option_1=q['option_1'],
                    option_2=q['option_2'],
                    option_3=q['option_3'],
                    option_4=q['option_4'],
                    correct_option=q['correct_option'],
                    blooms_taxonomy_level=q['blooms_taxonomy_level'],
                    elo_rating=get_initial_elo_rating(q['blooms_taxonomy_level'])
                )
                db.session.add(question)

        db.session.commit()
        print("Database initialized with test data.")

if __name__ == '__main__':
    init_db()