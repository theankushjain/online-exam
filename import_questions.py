import pandas as pd
from app import app
from models import db, Question
from elo import get_initial_elo_rating
from sqlalchemy.orm import scoped_session, sessionmaker

def import_questions_from_excel(file_path):
    df = pd.read_excel(file_path)
    
    with app.app_context():
        # Create a new scoped session
        session_factory = sessionmaker(bind=db.engine)
        Session = scoped_session(session_factory)
        
        for _, row in df.iterrows():
            # Create a new session for each question
            session = Session()
            try:
                blooms_level = int(row['Level of Bloom\'s Taxonomy'])
                initial_elo = get_initial_elo_rating(blooms_level)
                
                question = Question(
                    course=row['Course'],
                    topic=row['Topic'],
                    statement=row['Question Statement'],
                    option_1=row['Option 1'],
                    option_2=row['Option 2'],
                    option_3=row['Option 3'],
                    option_4=row['Option 4'],
                    correct_option=int(row['Correct Option']),
                    blooms_taxonomy_level=blooms_level,
                    elo_rating=initial_elo
                )
                session.add(question)
                session.commit()
                print(f"Added question: {question.statement[:30]}...")
            except Exception as e:
                session.rollback()
                print(f"Error adding question: {e}")
            finally:
                session.close()
        
        # Remove the scoped session
        Session.remove()

if __name__ == '__main__':
    import_questions_from_excel(r'C:\Users\ACER\Desktop\Projects\Exam Portal\PythonApp\exam_system_env\questions.xlsx')
    print("Questions import process completed.")