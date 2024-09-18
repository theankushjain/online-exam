from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    elo_rating = db.Column(db.Float, default=1500, nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    statement = db.Column(db.Text, nullable=False)
    option_1 = db.Column(db.String(200), nullable=False)
    option_2 = db.Column(db.String(200), nullable=False)
    option_3 = db.Column(db.String(200), nullable=False)
    option_4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)
    blooms_taxonomy_level = db.Column(db.Integer, nullable=False)
    elo_rating = db.Column(db.Float, nullable=False)

class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Float, default=0.0)
    elo_rating_change = db.Column(db.Float, default=0.0)
    
    student = db.relationship('Student', backref=db.backref('exam_attempts', lazy=True))

class ExamResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    time_taken = db.Column(db.Float, nullable=False)
    difficulty_feedback = db.Column(db.String(20), nullable=False)
    student_elo_rating_before = db.Column(db.Float, nullable=False)
    student_elo_rating_after = db.Column(db.Float, nullable=False)
    question_elo_rating_before = db.Column(db.Float, nullable=False)
    question_elo_rating_after = db.Column(db.Float, nullable=False)
    
    exam_attempt = db.relationship('ExamAttempt', backref=db.backref('responses', lazy=True))
    question = db.relationship('Question', backref=db.backref('responses', lazy=True))