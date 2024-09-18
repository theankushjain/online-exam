import math

def expected_score(rating_a, rating_b):
    return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

def update_elo(rating, expected, actual, k_factor=32):
    return rating + k_factor * (actual - expected)

def calculate_elo_changes(student_rating, question_rating, is_correct):
    expected_student = expected_score(student_rating, question_rating)
    expected_question = expected_score(question_rating, student_rating)
    
    actual_student = 1 if is_correct else 0
    actual_question = 1 - actual_student
    
    new_student_rating = update_elo(student_rating, expected_student, actual_student)
    new_question_rating = update_elo(question_rating, expected_question, actual_question)
    
    student_change = new_student_rating - student_rating
    question_change = new_question_rating - question_rating
    
    return student_change, question_change

def get_initial_elo_rating(blooms_level):
    elo_ratings = {1: 1300, 2: 1400, 3: 1500, 4: 1600, 5: 1700, 6: 1800}
    return elo_ratings.get(blooms_level, 1500)  # Default to 1200 if level is not found