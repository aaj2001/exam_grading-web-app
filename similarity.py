from fuzzywuzzy import fuzz# لحساب تشابة النصوص
import itertools # لاغراض التكرار

def calculate_levenshtein_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0# اذا اي من النصين مش موجود بنرجع 0.0
    return fuzz.token_sort_ratio(str(text1), str(text2)) / 100.0# بتقارن بين النصين بعد بترتب الكلمات على الابجدية  و بترجع نسبة التشابه بين 0 و 1

def calculate_jaccard_similarity(answers1, answers2):
    common_questions = set(answers1.keys()) & set(answers2.keys())# بنعمل تقاطع بين مجموعة اجوبة 1 ومجموعة اجوبة 2 عشان نطلع التشابة
    if not common_questions: # اذا ما كان في اسئلة مشتركة نرجع صفر
        return 0.0
    return sum(answers1[q] == answers2[q] for q in common_questions) / len(common_questions)# لكل سؤال مشترك بنقارن الاجابات,بتكون ترو او فولس, مع كل ترو بنجمع 1 وبنقسم على عدد الاسئلة المشتركة

def analyze_essays_levenshtein(reference_essay, student_essays):
    return {str(student): calculate_levenshtein_similarity(reference_essay, essay) 
            for student, essay in student_essays.items()}# المفتاح هو اسم الطالب

def analyze_mcq_jaccard(reference_answers, student_answers):
    results = {}# قاموس فاضي بنخزن فيه النتائج
    
    for student, answers in student_answers.items():
        common_questions = set(reference_answers.keys()) & set(answers.keys())# بنعمل تقاطع بين مجموعة اجوبة المرجعية ومجموعة اجوبة الطالب عشان نطلع التشابة
        correct_answers = sum(1 for q in common_questions if answers.get(q) == reference_answers.get(q))# نحسب كم سؤل كان الاجابة عليه صحيحة
        
        answer_comparison = {question: {
            'student_answer': answers.get(question, 'N/A'),
            'correct_answer': reference_answers.get(question, 'N/A'),
            'is_correct': answers.get(question) == reference_answers.get(question)
        } for question in reference_answers.keys()}
        
        results[str(student)] = {
            'similarity': calculate_jaccard_similarity(reference_answers, answers),
            'score': correct_answers,
            'total': len(reference_answers),
            'answers': answer_comparison,
            'student_raw_answers': answers
        }
    
    return results

def detect_cheating_essays(student_essays, threshold=0.8, strictness=0.5):
    threshold = max(0.0, min(1.0, float(threshold))) # ضبط القيمه لتكون بين 0 و 1
    strictness = max(0.0, min(1.0, float(strictness))) # ضبط القيمه لتكون بين 0 و 1
    
    if strictness > 0.7:  # ستركنس اعلى يعني اكثر فلاجينج
        adjusted_threshold = threshold * (1.0 - (strictness - 0.7) * 0.5)
    elif strictness < 0.3:  # ستركنس اقل يعني اقل فلاجينج    
        adjusted_threshold = threshold * (1.0 + (0.3 - strictness) * 0.5)
    else:
        adjusted_threshold = threshold# طبيعي
    
    adjusted_threshold = max(0.1, min(0.95, adjusted_threshold))
    #قاموس جديد فيه  البرايمري كي هو اسم الطالبين  وبقارن الاجابات بين كل طالبين وبنرجع نسبة التشابه
    return {f"{student_a} - {student_b}": calculate_levenshtein_similarity(student_essays[student_a], student_essays[student_b])
            for student_a, student_b in itertools.combinations(student_essays.keys(), 2) # تاخذ كل زوج مختلف  بدون تكرار من اسماء الطلاب
            if calculate_levenshtein_similarity(student_essays[student_a], student_essays[student_b]) >= adjusted_threshold}# يضاف الزوج الى القاموس بشرط اذا التشابة بين اجوبتهم اكبر او يساوي الثريشهولد

def detect_cheating_mcq(student_answers, threshold=0.8):
    threshold = max(0.0, min(1.0, float(threshold)))# لضمان قيمة الثريشهولد بين 0 و 1
            #قاموس جديد فيه  البرايمري كي هو اسم الطالبين  وبقارن الاجابات بين كل طالبين وبنرجع نسبة التشابه
    return {f"{student_a} - {student_b}": calculate_jaccard_similarity(student_answers[student_a], student_answers[student_b])
            for student_a, student_b in itertools.combinations(student_answers.keys(), 2)# تاخذ كل زوج مختلف  بدون تكرار من اسماء الطلاب
            if calculate_jaccard_similarity(student_answers[student_a], student_answers[student_b]) >= threshold}# يضاف الزوج الى القاموس بشرط اذا التشابة بين اجوبتهم اكبر او يساوي الثريشهولد