import logging
from fuzzywuzzy import fuzz
import itertools
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def calculate_levenshtein_similarity(text1, text2):
    """
    Calculate similarity between two texts using Levenshtein distance.
    Returns a normalized similarity score between 0 and 1, where 1 means identical texts.
    """
    try:
        # Ensure inputs are strings
        if not isinstance(text1, str):
            text1 = str(text1)
        if not isinstance(text2, str):
            text2 = str(text2)
            
        # Use fuzzywuzzy's token_sort_ratio which handles word order differences
        similarity = fuzz.token_sort_ratio(text1, text2) / 100.0
        return similarity
    except Exception as e:
        logging.error(f"Error calculating Levenshtein similarity: {str(e)}")
        return 0.0

def calculate_jaccard_similarity(answers1, answers2):
    """
    Calculate Jaccard similarity between two sets of MCQ answers.
    Returns a score between 0 and 1, where 1 means identical answer sets.
    """
    try:
        # Find common questions
        common_questions = set(answers1.keys()) & set(answers2.keys())
        
        if not common_questions:
            return 0.0
            
        # Count matching answers
        matches = sum(1 for q in common_questions if answers1[q] == answers2[q])
        
        # Calculate Jaccard similarity
        similarity = matches / len(common_questions) if common_questions else 0.0
        return similarity
    except Exception as e:
        logging.error(f"Error calculating Jaccard similarity: {str(e)}")
        return 0.0

def analyze_essays_levenshtein(reference_essay, student_essays):
    """
    Analyze student essays using Levenshtein distance.
    Returns similarity scores for each student.
    """
    results = {}
    
    for student, essay in student_essays.items():
        try:
            # Ensure student is a string
            student_key = student
            if not isinstance(student, str):
                student_key = str(student)
                
            similarity = calculate_levenshtein_similarity(reference_essay, essay)
            results[student_key] = similarity
        except Exception as e:
            logging.error(f"Error processing student essay {student}: {str(e)}")
            # Skip this student rather than failing the entire analysis
            continue
    
    return results

def analyze_mcq_jaccard(reference_answers, student_answers):
    """
    Analyze student MCQ answers using Jaccard similarity.
    Returns detailed results for each student including their answers for comparison.
    """
    results = {}
    
    for student, answers in student_answers.items():
        try:
            # Ensure student is a string
            student_key = student
            if not isinstance(student, str):
                student_key = str(student)
                
            # Calculate similarity
            similarity = calculate_jaccard_similarity(reference_answers, answers)
            
            # Calculate score
            common_questions = set(reference_answers.keys()) & set(answers.keys())
            correct_answers = sum(1 for q in common_questions 
                                if q in answers and answers[q] == reference_answers[q])
            total_questions = len(reference_answers)
            
            # Prepare comparison data for each question
            answer_comparison = {}
            for question in reference_answers.keys():
                correct_answer = reference_answers.get(question, 'N/A')
                student_answer = answers.get(question, 'N/A')
                is_correct = student_answer == correct_answer
                
                answer_comparison[question] = {
                    'student_answer': student_answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct
                }
            
            results[student_key] = {
                'similarity': similarity,
                'score': correct_answers,
                'total': total_questions,
                'answers': answer_comparison,  # Include the detailed answer comparison
                'student_raw_answers': answers  # Include the original student answers
            }
        except Exception as e:
            logging.error(f"Error processing student {student}: {str(e)}")
            # Skip this student rather than failing the entire analysis
            continue
    
    return results

def detect_cheating_essays(student_essays, threshold=0.8, strictness=0.5):
    """
    Detect potential cheating among student essays based on similarity threshold and strictness parameter.
    Returns a dictionary of suspicious pairs and their similarity scores.
    
    Args:
        student_essays (dict): Dictionary of student names/IDs to essay text
        threshold (float): Similarity threshold (0-1) for flagging suspicious pairs
                           Higher values are more strict (require more similarity)
                           Lower values are more lenient (flag more potential cases)
        strictness (float): How strictly to evaluate the similarity (0-1)
                            Low values (0.0-0.3) are more lenient, may ignore minor similarities
                            Medium values (0.4-0.7) provide balanced assessment
                            High values (0.8-1.0) are very strict, flag even minor similarities
    """
    suspicious_pairs = {}
    
    # Validate threshold is a float between 0 and 1
    try:
        threshold = float(threshold)
        threshold = max(0.0, min(1.0, threshold))  # Clamp to valid range
        logging.debug(f"Using cheating detection threshold: {threshold}")
    except (ValueError, TypeError):
        logging.warning(f"Invalid threshold value: {threshold}, using default 0.8")
        threshold = 0.8
        
    # Validate strictness is a float between 0 and 1
    try:
        strictness = float(strictness)
        strictness = max(0.0, min(1.0, strictness))  # Clamp to valid range
        logging.debug(f"Using strictness parameter: {strictness}")
    except (ValueError, TypeError):
        logging.warning(f"Invalid strictness value: {strictness}, using default 0.5")
        strictness = 0.5
        
    # Adjust the threshold based on strictness
    # In lower strictness, we might actually increase the threshold to be more lenient
    # In higher strictness, we might decrease the threshold to be more strict
    adjusted_threshold = threshold
    
    # Apply strictness effect (higher strictness = lower effective threshold = more flagging)
    if strictness > 0.7:  # High strictness, be more aggressive in flagging
        adjusted_threshold = threshold * (1.0 - (strictness - 0.7) * 0.5)  # Lower threshold up to 15%
    elif strictness < 0.3:  # Low strictness, be more lenient
        adjusted_threshold = threshold * (1.0 + (0.3 - strictness) * 0.5)  # Raise threshold up to 15%
        
    # Ensure threshold stays within valid bounds after adjustment
    adjusted_threshold = max(0.1, min(0.95, adjusted_threshold))
    
    logging.debug(f"Adjusted threshold due to strictness: {adjusted_threshold}")
    
    # Get all pairs of students
    student_pairs = list(itertools.combinations(student_essays.keys(), 2))
    logging.debug(f"Analyzing {len(student_pairs)} student pairs for potential cheating")
    
    for student_a, student_b in student_pairs:
        essay_a = student_essays[student_a]
        essay_b = student_essays[student_b]
        
        similarity = calculate_levenshtein_similarity(essay_a, essay_b)
        logging.debug(f"Similarity between {student_a} and {student_b}: {similarity:.4f}")
        
        # Use the adjusted threshold based on strictness parameter
        if similarity >= adjusted_threshold:
            # Ensure student names are strings before formatting
            student_a_str = str(student_a) if not isinstance(student_a, str) else student_a
            student_b_str = str(student_b) if not isinstance(student_b, str) else student_b
            pair_key = f"{student_a_str} - {student_b_str}"
            suspicious_pairs[pair_key] = similarity
            logging.debug(f"Potential cheating detected: {pair_key} (similarity: {similarity:.4f})")
    
    logging.info(f"Detected {len(suspicious_pairs)} suspicious pairs using adjusted threshold {adjusted_threshold} (original threshold: {threshold}, strictness: {strictness})")
    return suspicious_pairs

def detect_cheating_mcq(student_answers, threshold=0.8):
    """
    Detect potential cheating among MCQ answers based on similarity threshold.
    Returns a dictionary of suspicious pairs and their similarity scores.
    
    Args:
        student_answers (dict): Dictionary of student names/IDs to their MCQ answers
        threshold (float): Similarity threshold (0-1) for flagging suspicious pairs
                           Higher values are more strict (require more similarity)
                           Lower values are more lenient (flag more potential cases)
    """
    suspicious_pairs = {}
    
    # Validate threshold is a float between 0 and 1
    try:
        threshold = float(threshold)
        threshold = max(0.0, min(1.0, threshold))  # Clamp to valid range
        logging.debug(f"Using MCQ cheating detection threshold: {threshold}")
    except (ValueError, TypeError):
        logging.warning(f"Invalid threshold value: {threshold}, using default 0.8")
        threshold = 0.8
    
    # Get all pairs of students
    student_pairs = list(itertools.combinations(student_answers.keys(), 2))
    logging.debug(f"Analyzing {len(student_pairs)} student pairs for potential MCQ cheating")
    
    for student_a, student_b in student_pairs:
        answers_a = student_answers[student_a]
        answers_b = student_answers[student_b]
        
        similarity = calculate_jaccard_similarity(answers_a, answers_b)
        logging.debug(f"MCQ similarity between {student_a} and {student_b}: {similarity:.4f}")
        
        if similarity >= threshold:
            # Ensure student names are strings before formatting
            student_a_str = str(student_a) if not isinstance(student_a, str) else student_a
            student_b_str = str(student_b) if not isinstance(student_b, str) else student_b
            pair_key = f"{student_a_str} - {student_b_str}"
            suspicious_pairs[pair_key] = similarity
            logging.debug(f"Potential MCQ cheating detected: {pair_key} (similarity: {similarity:.4f})")
    
    logging.info(f"Detected {len(suspicious_pairs)} suspicious MCQ pairs using threshold {threshold}")
    return suspicious_pairs
