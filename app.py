import io  #بتحول السترينج لملف وبتتعامل مع الملفات بشكل مؤقت بدون التخزين علجهاز
import os
import csv
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename  # تنظيف اسم الملف من الرموز الغريبة
from werkzeug.security import generate_password_hash, check_password_hash  #generate password  بتشفر كلمة السر  وبتخزنها
#check password بتشفر كلمة السر وتتحقق من تطابقها مع كلمة السر المشفرة المخزنه
from functools import wraps  # عشان امنع الوصول للبيانات في حال اليوزر مش مسجل دخول
from similarity import analyze_essays_levenshtein, analyze_mcq_jaccard, detect_cheating_essays, detect_cheating_mcq

#create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "a_default_secret_key")

#database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = database_url  # database url لو موجود خزن الرابط باعدادات التطبيق
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True
    }  #pool cycle لو الاتصال استمر 500 ثانيه  البرنامج بعمل اعادة اتصال
# pool ping قبل ما يتصل ,بتاكد اذا الاتصال موجود يعني بعمل اختبار للاتصال
else:
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam_grader.db'  # لو الرابط مش موجود  استخدم قاعدة بيانات محلية

app.config[
    'SQLALCHEMY_TRACK_MODIFICATIONS'] = False  #sql بعطل مراقبة التعديلات عشان اوفر اداء افضل
db = SQLAlchemy(app)  # ربط قاعدة البيانات مع التطبيق

ALLOWED_EXTENSIONS = {'txt', 'csv'}


#database model
class User(db.Model):  # كلاس يوزر يمثل جدول بيانات
    # model هي بتنشىء جدول في قاعدة البيانات
    __tablename__ = 'user'  # اسم اول تيبل
    id = db.Column(db.Integer, primary_key=True)  # id هو برايمري كي
    username = db.Column(
        db.String(80), unique=True,
        nullable=False)  #nullable-false يعني لا يمكن ان يكون فارغ
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(
        db.String(255),
        nullable=False)  # password hash بتخزن كلمة السر المشفرة
    created_at = db.Column(db.DateTime,
                           default=datetime.utcnow)  #utcnow بتخزن الوقت الحالي


#database model2
class Exam(db.Model):  #كلاس امتحان يمثل جدول بيانات
    __tablename__ = 'exam'  #اسم ثاني تيبل
    id = db.Column(db.Integer, primary_key=True)  # id هو برايمري كي
    name = db.Column(db.String(100), nullable=False)  # اسم الامتحان مطلوب
    title = db.Column(db.String(200), nullable=True)  # nullable-true يعني يمكن ان يكون فارغ
    exam_type = db.Column(db.String(20), nullable=False)  #ملتبل او ايسساي
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  #utcnow بتخزن الوقت الحالي
    user_id = db.Column(db.Integer, nullable=True)
    reference_content = db.Column(db.Text, nullable=True)
    results_data = db.Column(db.Text, nullable=True)
    cheating_data = db.Column(db.Text, nullable=True)


#login required ديكوريتور عشان امنع الوصول للبيانات في حال اليوزر مش مسجل دخول
def login_required(f):

    @wraps(f)  #بتحافظ على اسم الدالة الاصليه لما نلفها
    def decorated_function(
            *args, **kwargs):  #args معطيات بدون اسم, kwargs معطيات مع اسم
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function  #بترجع الدالة الاصليه بعد ما نفك التغليف عنها


def allowed_file(filename):
    return filename and '.' in filename and filename.rsplit('.', 1)[1].lower(
    ) in ALLOWED_EXTENSIONS  #1اقسم الملف مره وحده من اليمين وخذ اندكس


def parse_file_content(content, is_csv):  #csv جيب نص محتوى الملف وتاكد انو
   #بتوخذ 2 ارجيومنت
    # وظيفة الفنكشن هي تحويل النص الى قاموس وبتحلل الاجابات
    result = {}  #افتح قاموس فارغ
    if is_csv:
        for row in csv.reader(io.StringIO(content)):
            if len(row) >= 2:  #بنتاكد انو علاقل في سطرين عشان الكود الجاي
                result[row[0].strip()] = row[1].strip(
                )  #باخد اول سطر واخر سطر وبحذف الفراغات من كل جانب
            # وبكون اول سطر هو برايمري كي واخر سطر هو قيمة البرايمري كي
    else:
        for line in content.strip().split('\n'):
            parts = line.split(':', 1)  #بنقسم السطر مره وحده من اليسار
            if len(parts) == 2:  # اذا انو جد بحتوي على قيمتين
                result[parts[0].strip()] = parts[1].strip(
                )  #باخد اول قيمة واخر قيمة وبحذف الفراغات من كل جانب
    return result


#authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # اذا كانت الميثود بوست , يعني اليوزر دخل بيانات
        #اقرا البيانات الادخلها اليوزر
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:  #من ملف html
            #اذا كلمة السر مش متطابقة
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first(
        ):  # دورلي بقاعدة البيانات في عمود يوزرنيم اذا فيه يوزرنيم متطابق لقيمة متغير يوزرنيم
            flash('Username already exists!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first(
        ):  # دورلي بقاعدة البيانات في عمود ايميل اذا فيه ايميل متطابق لقيمة متغير ايميل
            flash('Email already registered!', 'danger')
            return render_template('register.html')

        # اذا اليوزر مش موجود لازم يعمل تسجيل دخول
        try:
            password_hash = generate_password_hash(password)
            new_user = User()
            new_user.username = username
            new_user.email = email
            new_user.password_hash = password_hash
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback(
            )  # اعمل رول باك لقاعدة البيانات قبل وقوع الخطا
            flash('Registration failed. Please try again.', 'danger')
            return render_template('register.html')

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # اذا كانت الميثود بوست , يعني اليوزر دخل بيانات
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first(
        )  # ببحث في قاعدة البيانات عن يوزرنيم متطابق مع اليوزرنيم الادخله اليوزر وبجيب اول يوزر نيم مطابق

        if user and check_password_hash(
                user.password_hash, password
        ):  # اذا اليوزر موجود وكلمة السر متطابقة مع كلمة السر المشفرة في قاعدة البيانات
            session['user_id'] = user.id  # id خزنو في السيشن
            session['username'] = user.username  # يوزرنيم خزنو في السيشن
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()  # اخذف البيانات المخزنة في السيشن
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required  # في حال اليوزر مش مسجل دخول , بديكوريتور بتعمل ريديركت للصفحة الرئيسية
def dashboard():
    user = User.query.get(session['user_id'])#الاي دي اليوزر عمل لوج ان فيه بالسيشن واستخدمه لجلب معلومات اليوزر من قاعدة البيانات
    recent_exams = Exam.query.filter_by(user_id=user.id).order_by(Exam.created_at.desc()).limit(5).all() if user else []#فلتر الامتحانات الموجوده في قاعدة البيانات حسب ايدي اليوزر وربتها حسب الوقت تنازلي واخد اول 5 امتحانات
    return render_template('dashboard.html', user=user, recent_exams=recent_exams)


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


#initialize database tables
def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Database initialization error: {e}")


#call database initialization
init_db()#بتبدا في انشاء الجداول في قاعدة البيانات


@app.route('/start_analysis')
@login_required# في حال اليوزر مش مسجل دخول , بديكوريتور بتعمل ريديركت للصفحة الرئيسية
def start_analysis():
    #جيب نوع الاناليسيس من ال url
    analysis_type = request.args.get('type', None)

    #بنتاكد  ان نوع الاناليسيس هو مقالي او خيارات متعدد
    if analysis_type not in ['mcq', 'essay']:
        analysis_type = None

    return render_template('start_analysis.html', analysis_type=analysis_type)#html بتروح على صفحة الاناليسيس
                                                                                # وبتمررلها نوع الاناليسيس

@app.route('/mcq_analysis', methods=['GET', 'POST'])
@login_required# في حال اليوزر مش مسجل دخول , بديكوريتور بتعمل ريديركت للصفحة الرئيسية
def mcq_analysis():
    if request.method == 'POST':
        # بنتاكد من انو اليوزر ارسل ملف مرجعي
        if 'reference_file' not in request.files:
            flash('No reference file provided', 'danger')
            return redirect(request.url)
        # اذا ما تنفذ اشي من الفوق ,ارجع لصفحة تحميل الملف المرجعي
        reference_file = request.files['reference_file']

        if not reference_file or reference_file.filename == '':# اذا الملف مش موجود او اسم الملف فاضي
            flash('No reference file selected', 'danger')
            return redirect(request.url)

        if allowed_file(reference_file.filename):
            try:
                reference_content = reference_file.read().decode('utf-8')# utf-8 خذ البايتات الخزنها الموقع او الكومبيوتر وحولها لنص  فعلي
                is_csv = reference_file.filename and reference_file.filename.lower().endswith('.csv')#تحقق اذا اسم الملف موجود وامتدادو هو csv
                reference_answers = parse_file_content(reference_content, is_csv)
                session['reference_answers'] = reference_answers# احفظ البيانات بالسيشن
                flash('✓ Reference answers successfully uploaded! You can now upload student answers.', 'success')
                return render_template('mcq_analysis.html', reference_loaded=True, question_count=len(reference_answers))
            except Exception as e:
                flash(f'Error processing reference file: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Invalid file format. Please upload a TXT or CSV file',
                  'danger')
            return redirect(request.url)

    return render_template('mcq_analysis.html', reference_loaded=False)


@app.route('/process_mcq_answers', methods=['POST'])
def process_mcq_answers():
    if 'reference_answers' not in session:
        flash('Reference answers not found. Please upload reference answers first.', 'danger')
        return redirect(url_for('mcq_analysis'))

    student_files = request.files.getlist('student_files')#ناخذ كل الملفات الادخلها اليوزر على شكل قائمة
    
    if not student_files or student_files[0].filename == '':#اذا الملفات مش موجوده او اسم اول ملف فاضي
        flash('No student files selected', 'danger')
        return redirect(url_for('mcq_analysis'))

    if len(student_files) > 15:# اذا عدد الملفات الرفعها اليوزر اكثر من 15 ملف
        flash('Maximum 15 files allowed per submission. Please submit these files first, then add more if needed.', 'warning')
        return redirect(url_for('mcq_analysis'))

    similarity_threshold = 0.8# الثريشهولد لاسئلة الملتبل ثابت على 0.8

    reference_answers = session.get('reference_answers', {})# بحاول يرجع الاجابات المرجعية من السيشن واذا ما كان موجود رجع قاموس فاضي
    student_answers = {}# بجهز قاموس فارغ لاجابات الطلاب
    valid_files = 0# متغير (عدّاد)

    for student_file in student_files:
        if student_file and allowed_file(student_file.filename):# اذا الملف موجود وامتدادو مسموح
            try:
                filename = student_file.filename or ""# جيب اسم الفايل الرفعو الطالب واذا ما كان موجود رجع قيمة فاضيه
                student_name = secure_filename(filename)# secure_filename تنظيف اسم الملف من الرموز الغريبة
                if '.' in student_name:# اذا لسا موجود فيه امتداد
                    student_name = student_name.rsplit('.', 1)[0]# اقسم الاسم مره وحده من اليمين وخذ اول اندكس

                student_content = student_file.read().decode('utf-8')# اقرا محتوى الملف كبايتات وحولها لنص مفهوم 
                is_csv = filename.lower().endswith('.csv') if filename else False# بنتاكد اذا امتداد الفايل هو csv
                                                                    # "في حال الفايل موجود"
                answers = parse_file_content(student_content, is_csv)# تحليل اجابات الملف 

                student_answers[student_name] = answers# بتخزن الاجابات  بناءا على اسم الطالب وهو البرايمري كي
                valid_files += 1# انكريمنت 1 لعداد الملفات
            except Exception as e:
                flash(
                    f'Error processing file {student_file.filename}: {str(e)}',
                    'warning')

    if valid_files == 0:# اذا العداد ما مشى يعني ما كان في ملفات صالحة
        flash('No valid student files were processed', 'danger')
        return redirect(url_for('mcq_analysis'))

    # مقارنة الاجابات المرجعية مع اجابات الطلاب
    results = analyze_mcq_jaccard(reference_answers, student_answers)

    # كشف الغش بناءا علتشابه
    cheating_report = detect_cheating_mcq(student_answers, similarity_threshold)

    session['mcq_results'] = results
    session['mcq_reference_answers'] = reference_answers
    session['mcq_cheating_report'] = cheating_report
    # نخزن النتائج بالسيشن

    try:
        new_exam = Exam()# ننشىء كائن امتحان جديد
        new_exam.name = f"MCQ Analysis - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"# الاسم بكون النص + الوقت الحالي
        new_exam.exam_type = 'mcq'
        new_exam.user_id = session['user_id']# اربط اي دي اليوزر الحالي ب اي دي اليوزر العامل لوج ان
        new_exam.reference_content = json.dumps(reference_answers)# بنحول الريفرينس لنص منظم حتى نحفظهم كنص  داخل الداتا بيز
        new_exam.results_data = json.dumps(results) # بنحول النتائج لنص منظم حتى نحفظهم كنص  داخل الداتا بيز
        new_exam.cheating_data = json.dumps(cheating_report)# بنحول ريبورت الغش لنص منظم حتى نحفظهم كنص  داخل الداتا بيز

        db.session.add(new_exam)#بنضيف الامتحان الجديد لقاعدة البيانات بجلسة مؤقتة
        db.session.commit()# بننفذ الحفظ فعليا بقاعة البيانات
    except Exception as e:
        print(f"Error saving exam to database: {e}")

    return redirect(url_for('show_results', analysis_type='mcq'))


@app.route('/essay_analysis', methods=['GET', 'POST'])
@login_required# في حال اليوزر مش مسجل دخول , بديكوريتور بتعمل ريديركت للصفحة الرئيسية
def essay_analysis():
    if request.method == 'POST':
        #اذا اليوزر ما ارسل ملف مرجعي
        if 'reference_file' not in request.files:
            flash('No reference file provided', 'danger')
            return redirect(request.url)

        reference_file = request.files['reference_file']# خزن الملف الرفعو اليوزر بمتغير اسمو reference_file

        # اذا الملف المرجعي مش موجود او اسم الملف فاضي
        if not reference_file or reference_file.filename == '':
            flash('No reference file selected', 'danger')
            return redirect(request.url)

        if allowed_file(reference_file.filename):# اذا الملف مرجعي امتدادو مسموح
            try:
                reference_content = reference_file.read().decode('utf-8')# اقرا محتوى الملف كبايتات وحولها لنص مفهوم وخزنها بمتغير اسمو reference_content
                session['reference_essay'] = reference_content# بنخزن الملف المرجعي بالسيشن
                preview = (reference_content[:200] + '...') if len(reference_content) > 200 else reference_content# متغير جديد بنخزن فيه محتوى الملف المرجعي من اندكس 0 ل 199 ياجمالي 200 حرف
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
    if 'reference_essay' not in session:# اذا الملف المرجعي مش موجود بالسيشن
        flash('Reference essay not found. Please upload reference essay first.', 'danger')
        return redirect(url_for('essay_analysis'))

    student_files = request.files.getlist('student_files')#ناخذ كل الملفات الادخلها اليوزر على شكل قائمة

    if not student_files or student_files[0].filename == '':# اذا الملفات مش موجوده او اسم اول ملف فاضي
        flash('No student files selected', 'danger')
        return redirect(url_for('essay_analysis'))

    if len(student_files) > 15:# اذا عدد الملفات الرفعها اليوزر اكثر من 15 ملف
        flash('Maximum 15 files allowed per submission. Please submit these files first, then add more if needed.', 'warning')
        return redirect(url_for('essay_analysis'))

    try:
        cheating_threshold = float(request.form.get('cheating_threshold', 0.8))# ناخذ من الفورم قيمة الثريشهولد الادخلها اليوزر واذا ما حدد قيمة رجع 0.8 ك ديفولت
        strictness_parameter = float(request.form.get('strictness_parameter', 0.5))# ناخذ من الفورم قيمة الستركتنس الادخلها اليوزر واذا ما حدد قيمة رجع 0.5 ك ديفولت

        if not (0 <= cheating_threshold <= 1 and 0 <= strictness_parameter <= 1):
            raise ValueError("Parameters must be between 0 and 1")
    except ValueError:
        flash('Invalid parameters. Please enter values between 0 and 1.','danger')
        return redirect(url_for('essay_analysis'))

    #process student essays
    reference_essay = session.get('reference_essay', '')# بحاول يرجع الملف المرجعي من السيشن واذا ما كان موجود رجع قيمة فاضيه
    student_essays = {}# بجهز قاموس فارغ لاجابات الطلاب
    valid_files = 0 # متغير (عدّاد)

    for student_file in student_files:
        if student_file and allowed_file(student_file.filename): # اذا الملف موجود وامتدادو مسموح
            try:
                student_name = "Unknown" if not student_file.filename else secure_filename( student_file.filename)# حط الاسم غير معرف اذا اسم الفايل مش موجود, غير هيك جيب اسم الفايل ونظفو من الرموز الغريبة
                if '.' in student_name:# اذا لسا موجود فيه امتداد
                    student_name = student_name.rsplit('.', 1)[0]# اقسم الاسم مره وحده من اليمين وخذ اول اندكس اللي هو الاسم

                student_content = student_file.read().decode('utf-8') # اقرا محتوى الملف كبايتات وحولها لنص مفهوم
                student_essays[student_name] = student_content # بنخزن محتوى الملف بناءا على اسم الطالب وهو البرايمري كي
                valid_files += 1 # انكريمنت 1 لعداد الملفات
            except Exception as e:
                flash(
                    f'Error processing file {student_file.filename}: {str(e)}', 'warning')
                
    if valid_files == 0: # اذا العداد ما مشى يعني ما كان في ملفات صالحة
        flash('No valid student files were processed', 'danger')
        return redirect(url_for('essay_analysis'))

    results = analyze_essays_levenshtein(reference_essay, student_essays) # مقارنة الملف المرجعي مع ملفات الطلاب
    cheating_report = detect_cheating_essays(student_essays, cheating_threshold, strictness_parameter) # كشف الغش بناءا علتشابة

    session['essay_results'] = results
    session['essay_cheating_threshold'] = cheating_threshold
    session['essay_strictness_parameter'] = strictness_parameter
    session['essay_cheating_report'] = cheating_report
    session['essay_submissions'] = student_essays
    # نخزن النتائج بالسيشن

    try:
        new_exam = Exam()# ننشىء كائن امتحان جديد وهو اكزام يمثل جدول في قاعدة البيانات
        new_exam.name = f"Essay Analysis - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}" # الاسم بكون النص + الوقت الحالي
        new_exam.exam_type = 'essay'# نوع الامتحان هو ايسساي
        new_exam.user_id = session['user_id'] # اربط اي دي اليوزر الحالي في السيشن ب اي دي اليوزر العامل لوج ان
        new_exam.reference_content = reference_essay # يخزن الملف المرجعي  في عمود  في جدول الامتحان في قاعدة البيانات
        new_exam.results_data = json.dumps(results) # بنحول النتائج لنص منظم حتى نحفظهم كنص  داخل الداتا بيز
        new_exam.cheating_data = json.dumps(cheating_report) # بنحول ريبورت الغش لنص منظم حتى نحفظهم كنص  داخل الداتا بيز

        db.session.add(new_exam)# بنضيف الامتحان الجديد لقاعدة البيانات بجلسة مؤقتة
        db.session.commit() # بننفذ الحفظ فعليا بقاعة البيانات
    except Exception as e:
        print(f"Error saving exam to database: {e}")

    return redirect(url_for('show_results', analysis_type='essay'))


@app.route('/results/<analysis_type>')
@login_required # في حال اليوزر مش مسجل دخول , بديكوريتور بتعمل ريديركت للصفحة الرئيسية
def show_results(analysis_type):
    if analysis_type == 'mcq':# نوع الاناليسيس هو متعدد
        # جرب اول اشي جيب النتائج من السيشن
        results = session.get('mcq_results', None)
        reference_answers = session.get('mcq_reference_answers', None)
        cheating_report = session.get('mcq_cheating_report', None)

        # اذا مش موجوده بالسشن , جرب جيبها من قاعدة البيانات
        if not results:
            latest_exam = Exam.query.filter_by(user_id=session['user_id'], exam_type='mcq').order_by(Exam.created_at.desc()).first()# فلتر الامتحانات الموجوده في قاعدة البيانات حسب ايدي اليوزر الحالي بالسشن وربتها حسب الوقت تنازلي وخذ اجدد امتحان

            if latest_exam and latest_exam.results_data:# اذا الامتحان موجود و فيه بيانات نتائج في عمود results_data في قاعدة البيانات
                import json
                results = json.loads(latest_exam.results_data) #بنحول النص  المنظم جيسون في عمود result_data الى قاموس
                reference_answers = json.loads(latest_exam.reference_content) if latest_exam.reference_content else None# بحول النص  المنظم جيسون في عمود reference_content الى قاموس في حال الملف المرجعي كان موجود
                cheating_report = json.loads(latest_exam.cheating_data) if latest_exam.cheating_data else None# بحول النص  المنظم جيسون في عمود cheating_data الى قاموس في حال ريبورت الغش كان موجود

        if not results:# اذا ما كان في نتائج
            flash('No MCQ analysis results found. Please upload and analyze files first.', 'danger')
            return redirect(url_for('mcq_analysis'))

        # pre-sort the questions numerically for each student
        sorted_results = {} # قاموس فاضي بنخزن فيه النتائج بعد ما ننظمها
        # اعمل لوب عكل طالب وجيب بياناتهم
        for student, data in results.items(): # student بكون هو البرايمري كي 
            sorted_answers = {} # قاموس فاضي بنخزن فيه الاجابات بعد ما ننظمها
            question_nums = [] # قائمة فاضية بنخزن فيها ارقام الاسئلة

            # بنستخرج ارقام الاسئلة 
            for q in data['answers'].keys(): # بنمر على سؤال وبنوخذ اسماء المفاتيح
                try:
                    num = int(q[1:]) if q.startswith('Q') else float('inf') # q[1:] بنوخذ كل اشي بعد اول حرف, واللي هو رقم السؤال في حال السؤال ببلش ب حرف Q
                                                                # else float('inf") بنحط السؤال في اخر القائمة
                    question_nums.append((q, num))# بنضيف اسم السؤال ورقم السؤال للقائمة
                except (ValueError, IndexError):
                    question_nums.append((q, float('inf'))) 

            for q, _ in sorted(question_nums, key=lambda x: x[1]):# بنرتب القائمة بناءا على رقم السؤال
                sorted_answers[q] = data['answers'][q]

            # Create copy with sorted answers
            sorted_data = data.copy()# بنعمل كوبي للداتا 
            sorted_data['answers'] = sorted_answers# بنخزن الاجابات المنظمة في الكوبي مع برايمري كي هو الاجابات
            sorted_results[student] = sorted_data# وبنخزن الكوبي في القاموس الجديد مع برايمري كي هو اسم الطالب

        return render_template('results.html', analysis_type='mcq', results=sorted_results,reference_answers=reference_answers,
                               cheating_report=cheating_report)

    elif analysis_type == 'essay':# نوع الاناليسيس هو ايسساي
        #اول اشي بنجرب ناخذ الداتا من السيشن
        results = session.get('essay_results', None)
        reference_essay = session.get('reference_essay')
        cheating_report = session.get('essay_cheating_report')
        cheating_threshold = session.get('essay_cheating_threshold', 0.8)
        strictness_parameter = session.get('essay_strictness_parameter', 0.5)

        # اذا مش بالسيشن , بنجرب ناخذها من قاعدة البيانات
        if not results:
            latest_exam = Exam.query.filter_by(user_id=session['user_id'], exam_type='essay').order_by(Exam.created_at.desc()).first()# فلتر الامتحانات الموجوده في قاعدة البيانات حسب ايدي اليوزر الحالي بالسشن وربتها حسب الوقت تنازلي وخذ اجدد امتحان

            if latest_exam and latest_exam.results_data: # اذا الامتحان موجود و فيه بيانات نتائج في عمود results_data في قاعدة البيانات
                import json
                results = json.loads(latest_exam.results_data) #بنحول النص  المنظم جيسون في عمود result_data الى قاموس
                reference_essay = latest_exam.reference_content# بنخزن الملف المرجعي في متغير
                cheating_report = json.loads(latest_exam.cheating_data) if latest_exam.cheating_data else None # بنحول النص  المنظم جيسون في عمود cheating_data الى قاموس في حال ريبورت الغش كان موجود
                # قيم ديفولت لما نحمل قاعدة البيانات
                cheating_threshold = 0.8
                strictness_parameter = 0.5

        if not results: # اذا ما كان في نتائج
            flash('No essay analysis results found. Please upload and analyze files first.', 'danger')
            return redirect(url_for('essay_analysis'))

        return render_template('results.html',  analysis_type='essay',  results=results,  reference_essay=reference_essay,
                               cheating_report=cheating_report,
                               cheating_threshold=cheating_threshold,
                               strictness_parameter=strictness_parameter)

    else:
        flash('Invalid analysis type', 'danger')
        return redirect(url_for('index'))


@app.route('/download_results/<analysis_type>')
def download_results(analysis_type):# تنزيل النتائج
    # اول اشي بنجرب ناخذ الداتا من السيشن
    results = session.get(f'{analysis_type}_results')
    cheating_report = session.get(f'{analysis_type}_cheating_report')

    if not results: # اذا ما كان في نتائج
        flash(f'No {analysis_type} results found', 'danger')
        return redirect(url_for('index'))

    # Create CSV output
    output = io.StringIO() #بنعمل ملف مؤقت في الذاكره
    writer = csv.writer(output)# مشان نكتب الناتج بصيغة csv    

    if analysis_type == 'mcq':
        writer.writerow(['Student', 'Score', 'Similarity Score']) # بنكتب  صف جديد فيه رؤوس الاعمده
        for student, data in results.items():
            writer.writerow([student, f"{data['score']}/{data['total']}", f"{data['similarity']:.2f}"]) # بنكتب  صف جديد فيه  3 اعمده همو الطالب, نتيجتو على التوتال و نسبة التشابه
                                                                                                # .2f  تعني عرض الرقم بمنزلتين بعد الفاصلة
    else:  #للايسساي
        writer.writerow(['Student', 'Similarity Score']) # بنكتب  صف جديد في رؤوس الاعمده
        for student, similarity in results.items(): # بنمر على كل طالب وناخذ اسمو ونسبة التشابه
            writer.writerow([student, f"{similarity:.2f}"]) # بنكتب  صف جديد فيه  2 اعمده همو الطالب و نسبة التشابه

    # سطر فارغ للفصل بين  البيانات
    writer.writerow([])

    # بنضيف ريبورت الغش اذا موجود 
    if cheating_report: # اذا في ريبورت غش
        writer.writerow(['High Similarity Between Student Submissions']) # بنكتب  صف جديد فيه  نص
        writer.writerow(['Student A', 'Student B', 'Similarity'])# بنكتب  صف جديد فيه  3 اعمده همو الطالب الاول, الطالب الثاني و نسبة التشابه

        for pair, similarity in cheating_report.items(): # for pair لطالبين 
            student_a, student_b = pair.split(' - ') #  بفصل الاسمين  عن بعض بعدل اول -
            if analysis_type = 'essay':
                student_a_content= session.get('essay_submissions', {}).get(student_a, 'Content not found')
            else:
                student_a_answers = results.get(student_a, {}).get('student_raw_answers', {})
            writer.writerow([student_a, student_b, f"{similarity:.2f}"]) # بنكتب  صف جديد فيه  3 اعمده همو الطالب الاول, الطالب الثاني و نسبة التشابه

    # تجهيز تنزيل الملف
    output.seek(0) # بنرجع لبداية الملف عشان  يكون محتوى الملف موجود كامل بس ننزلو
    # بنحول النص لبايتات ,بيعرف المتصفح انو ملف csv ,  بنخلي الملف يتحمل بدل ما ينعرض,اسم الملف بس ينزل بكون نوع الاناليسيس مع تكملة
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name=f'{analysis_type}_analysis_results.csv')
