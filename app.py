from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response, flash
from models import db, Student, Question, ExamAttempt, ExamResponse
from elo import calculate_elo_changes, get_initial_elo_rating
import random
import csv
import io
from datetime import datetime
import logging

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam_system.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

logging.basicConfig(level=logging.DEBUG)

def create_tables():
    with app.app_context():
        db.create_all()
        logging.info("Database tables created.")

def get_next_question(student):
    logging.debug(f"Getting next question for student {student.id}")
    if 'exam_attempt_id' not in session:
        logging.error("No exam_attempt_id in session")
        return None
    
    answered_questions = ExamResponse.query.filter_by(exam_attempt_id=session['exam_attempt_id']).with_entities(ExamResponse.question_id).all()
    answered_question_ids = [q.question_id for q in answered_questions]
    
    logging.debug(f"Already answered questions: {answered_question_ids}")
    
    eligible_questions = Question.query.filter(
        Question.id.notin_(answered_question_ids),
        Question.elo_rating.between(student.elo_rating - 100, student.elo_rating + 100)
    ).all()
    
    logging.debug(f"Number of eligible questions: {len(eligible_questions)}")
    
    if eligible_questions:
        return random.choice(eligible_questions)
    else:
        logging.debug("No eligible questions found")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if Student.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if Student.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        new_student = Student(username=username, email=email)
        new_student.set_password(password)
        db.session.add(new_student)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        student = Student.query.filter_by(username=username).first()
        if student and student.check_password(password):
            session['student_id'] = student.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('student_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    logging.debug("Entering dashboard route")
    if 'student_id' not in session:
        logging.debug("No student_id in session, redirecting to login")
        return redirect(url_for('login'))
    
    logging.debug(f"Fetching student with id {session['student_id']}")
    student = Student.query.get(session['student_id'])
    
    if student is None:
        logging.error(f"No student found with id {session['student_id']}")
        flash('Student not found. Please log in again.')
        return redirect(url_for('logout'))
    
    logging.debug(f"Student found: {student.username}")
    logging.debug(f"Student Elo rating: {student.elo_rating}")
    
    logging.debug("Fetching exam attempts")
    exam_attempts = ExamAttempt.query.filter_by(student_id=student.id).order_by(ExamAttempt.start_time.desc()).all()
    logging.debug(f"Number of exam attempts: {len(exam_attempts)}")
    
    for attempt in exam_attempts:
        logging.debug(f"Attempt ID: {attempt.id}, Score: {attempt.score}, Elo change: {attempt.elo_rating_change}")
    
    return render_template('dashboard.html', student=student, exam_attempts=exam_attempts)

@app.route('/start_exam')
def start_exam():
    logging.debug("Starting new exam")
    if 'student_id' not in session:
        logging.debug("No student_id in session, redirecting to login")
        return redirect(url_for('login'))
    
    student = Student.query.get(session['student_id'])
    if not student:
        logging.error(f"No student found with id {session['student_id']}")
        flash('Student not found. Please log in again.')
        return redirect(url_for('logout'))

    exam_attempt = ExamAttempt(student_id=student.id)
    db.session.add(exam_attempt)
    db.session.commit()
    
    session['exam_attempt_id'] = exam_attempt.id
    session['questions_answered'] = 0
    
    logging.debug(f"Created new exam attempt with id {exam_attempt.id}")
    
    # Check if there are any eligible questions
    question = get_next_question(student)
    if not question:
        logging.warning("No eligible questions found for this student")
        flash('No eligible questions found. Please contact the administrator.')
        return redirect(url_for('dashboard'))

    return redirect(url_for('exam'))

@app.route('/exam')
def exam():
    logging.debug("Entering exam route")
    if 'student_id' not in session or 'exam_attempt_id' not in session:
        logging.debug("Missing student_id or exam_attempt_id in session, redirecting to login")
        return redirect(url_for('login'))
    
    if session['questions_answered'] >= 10:
        logging.debug("All questions answered, redirecting to results")
        return redirect(url_for('results'))
    
    student = Student.query.get(session['student_id'])
    question = get_next_question(student)
    
    if question:
        logging.debug(f"Rendering question {question.id}")
        return render_template('exam.html', question=question, question_number=session['questions_answered'] + 1)
    else:
        logging.debug("No more questions available, redirecting to results")
        return redirect(url_for('results'))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'student_id' not in session or 'exam_attempt_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    student = Student.query.get(session['student_id'])
    question = Question.query.get(request.form['question_id'])
    selected_option = int(request.form['selected_option'])
    time_taken = float(request.form['time_taken'])
    difficulty_feedback = request.form['difficulty_feedback']

    is_correct = (selected_option == question.correct_option)

    student_rating_change, question_rating_change = calculate_elo_changes(
        student.elo_rating, question.elo_rating, is_correct)

    response = ExamResponse(
        exam_attempt_id=session['exam_attempt_id'],
        question_id=question.id,
        selected_option=selected_option,
        is_correct=is_correct,
        time_taken=time_taken,
        difficulty_feedback=difficulty_feedback,
        student_elo_rating_before=student.elo_rating,
        student_elo_rating_after=student.elo_rating + student_rating_change,
        question_elo_rating_before=question.elo_rating,
        question_elo_rating_after=question.elo_rating + question_rating_change
    )
    db.session.add(response)

    old_question_rating = question.elo_rating
    student.elo_rating += student_rating_change
    question.elo_rating += question_rating_change
    db.session.commit()

    session['questions_answered'] += 1

    if session['questions_answered'] >= 10:
        return jsonify({"redirect": url_for('results')})

    next_question = get_next_question(student)
    if next_question:
        return jsonify({
            "next_question": {
                "id": next_question.id,
                "statement": next_question.statement,
                "option_1": next_question.option_1,
                "option_2": next_question.option_2,
                "option_3": next_question.option_3,
                "option_4": next_question.option_4
            },
            "question_number": session['questions_answered'] + 1,
            "previous_question_update": {
                "old_rating": old_question_rating,
                "new_rating": question.elo_rating
            }
        })
    else:
        return jsonify({"redirect": url_for('results')})

@app.route('/results')
def results():
    logging.debug("Entering results route")
    if 'student_id' not in session or 'exam_attempt_id' not in session:
        logging.debug("Missing student_id or exam_attempt_id in session, redirecting to login")
        return redirect(url_for('login'))

    student = Student.query.get(session['student_id'])
    exam_attempt = ExamAttempt.query.get(session['exam_attempt_id'])
    
    if not exam_attempt:
        logging.error(f"No exam attempt found with id {session['exam_attempt_id']}")
        flash('No exam attempt found. Please start a new exam.')
        return redirect(url_for('dashboard'))

    responses = ExamResponse.query.filter_by(exam_attempt_id=exam_attempt.id).order_by(ExamResponse.id).all()
    
    if not responses:
        logging.warning("No responses found for this exam attempt")
        flash('No questions were answered in this exam attempt.')
        return redirect(url_for('dashboard'))

    correct_answers = sum(1 for response in responses if response.is_correct)
    total_questions = len(responses)
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    exam_attempt.end_time = datetime.utcnow()
    exam_attempt.score = score
    exam_attempt.elo_rating_change = student.elo_rating - responses[0].student_elo_rating_before
    db.session.commit()

    question_details = []
    for response in responses:
        question = Question.query.get(response.question_id)
        question_details.append({
            'statement': question.statement,
            'correct_option': question.correct_option,
            'selected_option': response.selected_option,
            'is_correct': response.is_correct,
            'old_rating': response.question_elo_rating_before,
            'new_rating': response.question_elo_rating_after
        })

    session.pop('exam_attempt_id', None)
    session.pop('questions_answered', None)

    logging.debug(f"Rendering results for student {student.id}, score: {score}")
    return render_template('results.html', 
                           student=student, 
                           initial_elo=responses[0].student_elo_rating_before,
                           score=score, 
                           correct_answers=correct_answers, 
                           total_questions=total_questions,
                           question_details=question_details)
@app.route('/export_data')
def export_data():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([
        'Student ID', 'Question ID', 'Selected Option', 'Is Correct', 'Time Taken',
        'Difficulty Feedback', 'Timestamp', 'Student Elo Rating Before',
        'Student Elo Rating After', 'Question Elo Rating Before',
        'Question Elo Rating After'
    ])
    
    responses = ExamResponse.query.all()
    for response in responses:
        cw.writerow([
            response.exam_attempt.student_id,
            response.question_id,
            response.selected_option,
            response.is_correct,
            response.time_taken,
            response.difficulty_feedback,
            response.exam_attempt.start_time,
            response.student_elo_rating_before,
            response.student_elo_rating_after,
            response.question_elo_rating_before,
            response.question_elo_rating_after
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=exam_data.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)