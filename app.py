import io
import os
import csv
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
#!session! مكان لتخزين بيانات مؤقتة
from werkzeug.utils import secure_filename
from similarity import (
    analyze_essays_levenshtein, 
    analyze_mcq_jaccard, 
    detect_cheating_essays, 
    detect_cheating_mcq
)

# create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "a_default_secret_key")    

# configure file upload
ALLOWED_EXTENSIONS = {'txt', 'csv'}

def allowed_file(filename):
    """Check if filename has an allowed extension"""
    if not filename:
        return False
    if '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    #!rsplit('.', 1)! بقسم اسم الفايل بعد  اول نقطه بشوفها مره وحده
    #!بصير !اسم الملف , الاكستنشن
    # ![1]! بيوخذ الجزس اليمين بعد القسم     
def parse_file_content(content, is_csv):
    """Parse file content based on format"""
    result = {}
    if is_csv:
        csv_reader = csv.reader(io.StringIO(content))
        #!StringIO! بحول النص  العادي  لملف مفتوح عشان نقرا ملف ال csv
        for row in csv_reader:
            if len(row) >= 2:
                result[row[0].strip()] = row[1].strip()
                #strip لمسح الفراغات من الاول والاخير
    else:  # text file
        lines = content.strip().split('\n')
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                result[parts[0].strip()] = parts[1].strip()
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_analysis')
def start_analysis():
    # get analysis type 
    analysis_type = request.args.get('type', None)
    
    # validate the type
    if analysis_type not in ['mcq', 'essay']:
        analysis_type = None
        
    return render_template('start_analysis.html', analysis_type=analysis_type)

@app.route('/mcq_analysis', methods=['GET', 'POST'])
def mcq_analysis():
    if request.method == 'POST':
        # check if the post request has the reference file
        if 'reference_file' not in request.files:
            flash('No reference file provided', 'danger')
            return redirect(request.url)
        
        reference_file = request.files['reference_file']
        
        # if user does not select a file, browser also submits an empty file
        if not reference_file or reference_file.filename == '':
            flash('No reference file selected', 'danger')
            return redirect(request.url)
        
        if allowed_file(reference_file.filename):
            try:
                # read reference answers
                reference_content = reference_file.read().decode('utf-8')
                #!decode('utf-8')! بتحول البايتس لسترينج
                #HTTP file uploads are binary by default
                # parse file based on extension
                is_csv = reference_file.filename and reference_file.filename.lower().endswith('.csv')
                #بنتاكد اول اذا الملف مش فاضي بعدين بنحط and بنتاكد اذا الاكستنشن csv
                reference_answers = parse_file_content(reference_content, is_csv)
                
                # store in session for later
                session['reference_answers'] = reference_answers
                
                flash('✓ Reference answers successfully uploaded! You can now upload student answers.', 'success')
                return render_template('mcq_analysis.html', 
                                      reference_loaded=True, 
                                      question_count=len(reference_answers))
            
            except Exception as e:
                flash(f'Error processing reference file: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Invalid file format. Please upload a TXT or CSV file', 'danger')
            return redirect(request.url)
    
    return render_template('mcq_analysis.html', reference_loaded=False)

@app.route('/process_mcq_answers', methods=['POST'])
def process_mcq_answers():
    if 'reference_answers' not in session:
        flash('Reference answers not found. Please upload reference answers first.', 'danger')
        return redirect(url_for('mcq_analysis'))
    
    if 'student_files' not in request.files:
        flash('No student files provided', 'danger')
        return redirect(url_for('mcq_analysis'))
    
    student_files = request.files.getlist('student_files')
    
    if not student_files or student_files[0].filename == '':#نتحقق من اول ملف فقط لانو المتصفحفي حال ما رفعت ولا ملف ... برسل ملف فاضي
        flash('No student files selected', 'danger')
        return redirect(url_for('mcq_analysis'))
        
    if len(student_files) > 15:
        flash('Maximum 15 files allowed per submission. Please submit these files first, then add more if needed.', 'warning')#warning للتنبيه الخفيف
        return redirect(url_for('mcq_analysis'))
        
    similarity_threshold = 0.8  # fixed threshold value
    
    reference_answers = session.get('reference_answers', {})
    student_answers = {}
    valid_files = 0
    
    for student_file in student_files:
        if student_file and allowed_file(student_file.filename):
            try:
                # extract student name 
                filename = student_file.filename or ""
                student_name = secure_filename(filename)#!secure_filename! بتشيل الرموز الغريبة
                if '.' in student_name:
                    student_name = student_name.rsplit('.', 1)[0]#بيقسم اسم الفايل بعد اول نقطه وبيوخذ الجزء اليمين
                
                student_content = student_file.read().decode('utf-8')#!decode('utf-8')! بتحول البايتس لسترينج
                
                is_csv = filename.lower().endswith('.csv') if filename else False
                answers = parse_file_content(student_content, is_csv)
                
                student_answers[student_name] = answers
                valid_files += 1
                
            except Exception as e:
                flash(f'Error processing file {student_file.filename}: {str(e)}', 'warning')

    
    if valid_files == 0:
        flash('No valid student files were processed', 'danger')
        return redirect(url_for('mcq_analysis'))
    
    # analyze student answers comparing to reference answers
    results = analyze_mcq_jaccard(reference_answers, student_answers)
    
    # detect potential cheating in mcq answers
    cheating_report = detect_cheating_mcq(student_answers, similarity_threshold)
    
    session['mcq_results'] = results#!session! بنخزن فيها قيم rsult,ref ans,cheat rep 
    session['mcq_reference_answers'] = reference_answers
    session['mcq_cheating_report'] = cheating_report
    #طول ما اليوزر ما عمل ريلود للصفحه ... هتكون البيانات موجوده في السيشن
    
    return redirect(url_for('show_results', analysis_type='mcq'))#بنوديه عصفحة النتائج

@app.route('/essay_analysis', methods=['GET', 'POST'])
def essay_analysis():
    if request.method == 'POST':
        # check if the post request has the reference file
        if 'reference_file' not in request.files:
            flash('No reference file provided', 'danger')
            return redirect(request.url)
        
        reference_file = request.files['reference_file']
        
        # if user does not select a file, browser also submits an empty file
        if not reference_file or reference_file.filename == '':
            flash('No reference file selected', 'danger')
            return redirect(request.url)
        
        if allowed_file(reference_file.filename):
            try:
                # read reference essay
                reference_content = reference_file.read().decode('utf-8')
                
                # store in session for later use
                session['reference_essay'] = reference_content
                
                preview = (reference_content[:200] + '...') if len(reference_content) > 200 else reference_content# تعبير شرطي بسطر واحد
                flash('✓ Reference essay successfully uploaded! You can now upload student essays.', 'success')
                return render_template('essay_analysis.html', reference_loaded=True, preview=preview)
            
            except Exception as e:
                flash(f'Error processing reference file: {str(e)}', 'danger')

                return redirect(request.url)
        else:
            flash('Invalid file format. Please upload a TXT file', 'danger')
            return redirect(request.url)
    
    return render_template('essay_analysis.html', reference_loaded=False)

@app.route('/process_essays', methods=['POST'])
def process_essays():
    if 'reference_essay' not in session:
        flash('Reference essay not found. Please upload reference essay first.', 'danger')
        return redirect(url_for('essay_analysis'))
    
    if 'student_files' not in request.files:
        flash('No student files provided', 'danger')
        return redirect(url_for('essay_analysis'))
    
    student_files = request.files.getlist('student_files')
    
    if not student_files or student_files[0].filename == '':
        flash('No student files selected', 'danger')
        return redirect(url_for('essay_analysis'))
        
    # enforce a limit of 15 files per submission
    if len(student_files) > 15:
        flash('Maximum 15 files allowed per submission. Please submit these files first, then add more if needed.', 'warning')
        return redirect(url_for('essay_analysis'))
    
    # get thresholds with validation
    try:
        cheating_threshold = float(request.form.get('cheating_threshold', 0.8))
        strictness_parameter = float(request.form.get('strictness_parameter', 0.5))
        
        if not (0 <= cheating_threshold <= 1 and 0 <= strictness_parameter <= 1):
            raise ValueError("Parameters must be between 0 and 1")
    except ValueError:
        flash('Invalid parameters. Please enter values between 0 and 1.', 'danger')
        return redirect(url_for('essay_analysis'))
    
    # process student essays
    reference_essay = session.get('reference_essay', '')
    student_essays = {}
    valid_files = 0
    
    for student_file in student_files:
        if student_file and allowed_file(student_file.filename):
            try:
                # extract student name  (handling none case)
                #في حال ما رفعت ملفات بدون اسم ... بنحط اسم غير معروف 
                if not student_file.filename:# بتحقق اذا اسم الفايل فاضي
                    student_name = "Unknown"
                else:
                    student_name = secure_filename(student_file.filename)
                    if '.' in student_name:
                        student_name = student_name.rsplit('.', 1)[0]
                    
                student_content = student_file.read().decode('utf-8')
                student_essays[student_name] = student_content
                valid_files += 1
            except Exception as e:
                flash(f'Error processing file {student_file.filename}: {str(e)}', 'warning')

    
    if valid_files == 0:
        flash('No valid student files were processed', 'danger')
        return redirect(url_for('essay_analysis'))
    
    # analyze student essays and detect potential cheating
    results = analyze_essays_levenshtein(reference_essay, student_essays)
    cheating_report = detect_cheating_essays(student_essays, cheating_threshold, strictness_parameter)
    
    # store results in session
    session['essay_results'] = results
    session['essay_cheating_threshold'] = cheating_threshold
    session['essay_strictness_parameter'] = strictness_parameter
    session['essay_cheating_report'] = cheating_report
    
     # redirect to results page
    return redirect(url_for('show_results', analysis_type='essay'))

@app.route('/results/<analysis_type>')
def show_results(analysis_type):
    if analysis_type == 'mcq':
        results = session.get('mcq_results', None)
        reference_answers = session.get('mcq_reference_answers', None)
        cheating_report = session.get('mcq_cheating_report', None)
        
        if not results:
            flash('No MCQ analysis results found. Please upload and analyze files first.', 'danger')
            return redirect(url_for('mcq_analysis'))
            
        # pre-sort the questions numerically for each student
        sorted_results = {}
        for student, data in results.items():
            sorted_answers = {}
            question_nums = []
            
            # Extract question numbers and prepare for sorting
            for q in data['answers'].keys():
                try:
                    num = int(q[1:]) if q.startswith('Q') else float('inf')
                    question_nums.append((q, num))
                except (ValueError, IndexError):
                    question_nums.append((q, float('inf')))
            
            # Sort by numeric value and rebuild answers dict
            for q, _ in sorted(question_nums, key=lambda x: x[1]):
                sorted_answers[q] = data['answers'][q]
            
            # Create copy with sorted answers
            sorted_data = data.copy()
            sorted_data['answers'] = sorted_answers
            sorted_results[student] = sorted_data
            
        return render_template('results.html', 
                              analysis_type='mcq', 
                              results=sorted_results, 
                              reference_answers=reference_answers,
                              cheating_report=cheating_report)
    
    elif analysis_type == 'essay':
        results = session.get('essay_results', None)
        
        if not results:
            flash('No essay analysis results found. Please upload and analyze files first.', 'danger')
            return redirect(url_for('essay_analysis'))
            
        return render_template('results.html', 
                              analysis_type='essay', 
                              results=results, 
                              reference_essay=session.get('reference_essay'),
                              cheating_report=session.get('essay_cheating_report'),
                              cheating_threshold=session.get('essay_cheating_threshold', 0.8),
                              strictness_parameter=session.get('essay_strictness_parameter', 0.5))
    
    else:
        flash('Invalid analysis type', 'danger')
        return redirect(url_for('index'))

@app.route('/download_results/<analysis_type>')
def download_results(analysis_type):
    # Get appropriate results based on analysis type
    results = session.get(f'{analysis_type}_results')
    cheating_report = session.get(f'{analysis_type}_cheating_report')
    
    if not results:
        flash(f'No {analysis_type} results found', 'danger')
        return redirect(url_for('index'))
    
    # Create CSV output
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write appropriate headers and data based on analysis type
    if analysis_type == 'mcq':
        writer.writerow(['Student', 'Score', 'Similarity Score'])
        for student, data in results.items():
            writer.writerow([student, f"{data['score']}/{data['total']}", f"{data['similarity']:.2f}"])
    else:  # essay
        writer.writerow(['Student', 'Similarity Score'])
        for student, similarity in results.items():
            writer.writerow([student, f"{similarity:.2f}"])
    
    # Add blank row between sections
    writer.writerow([])
    
    # Add cheating detection section if report exists
    if cheating_report:
        writer.writerow(['High Similarity Between Student Submissions'])
        writer.writerow(['Student A', 'Student B', 'Similarity'])
        
        for pair, similarity in cheating_report.items():
            student_a, student_b = pair.split(' - ')
            writer.writerow([student_a, student_b, f"{similarity:.2f}"])
    
    # Prepare file for download
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{analysis_type}_analysis_results.csv'
    )
