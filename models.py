from datetime import datetime
from main import db

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(20), nullable=False)  # 'mcq' or 'essay'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference_file = db.Column(db.Text, nullable=True)  # Store reference content
    results = db.relationship('Result', backref='exam', lazy=True)

    def __repr__(self):
        return f'<Exam {self.name}>'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), nullable=True, unique=True)
    results = db.relationship('Result', backref='student', lazy=True)

    def __repr__(self):
        return f'<Student {self.name}>'

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)  # 0-1 score
    submission_content = db.Column(db.Text, nullable=True)  # Store student's submission
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Result {self.exam_id} {self.student_id}>'

class CheatingDetection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student1_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student2_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)  # 0-1 score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student1 = db.relationship('Student', foreign_keys=[student1_id])
    student2 = db.relationship('Student', foreign_keys=[student2_id])
    exam = db.relationship('Exam')

    def __repr__(self):
        return f'<CheatingDetection {self.exam_id} {self.student1_id} {self.student2_id}>'
