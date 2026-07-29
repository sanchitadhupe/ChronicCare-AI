"""
Database Models for Chronic Disease Monitoring Application
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    """User authentication model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    profile = db.relationship('PatientProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    health_records = db.relationship('HealthRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    medications = db.relationship('Medication', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_history = db.relationship('ChatHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    medical_reports = db.relationship('MedicalReport', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class PatientProfile(db.Model):
    """Patient profile with chronic disease information"""
    __tablename__ = 'patient_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(150))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    blood_group = db.Column(db.String(10))
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(150))
    emergency_phone = db.Column(db.String(20))

    # Chronic Disease Information
    chronic_conditions = db.Column(db.Text)      # JSON list of conditions
    allergies = db.Column(db.Text)               # JSON list of allergies
    family_history = db.Column(db.Text)          # JSON list of family history

    # Lifestyle
    smoking_status = db.Column(db.String(50))
    alcohol_consumption = db.Column(db.String(50))
    physical_activity = db.Column(db.String(50))
    diet_type = db.Column(db.String(50))

    # Doctors
    primary_doctor = db.Column(db.String(150))
    doctor_phone = db.Column(db.String(20))
    hospital = db.Column(db.String(200))

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None

    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi is None:
            return "Unknown"
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    def __repr__(self):
        return f'<PatientProfile {self.full_name}>'


class HealthRecord(db.Model):
    """Daily health monitoring records"""
    __tablename__ = 'health_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Vital Signs
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)
    blood_sugar = db.Column(db.Float)        # mg/dL
    blood_sugar_type = db.Column(db.String(20))  # fasting / post-meal / random
    temperature = db.Column(db.Float)        # Celsius
    oxygen_saturation = db.Column(db.Float)  # SpO2 %
    weight_kg = db.Column(db.Float)

    # Symptoms
    symptoms = db.Column(db.Text)            # JSON list
    symptom_severity = db.Column(db.Integer)  # 1-10 scale
    pain_level = db.Column(db.Integer)       # 0-10 scale

    # Mood & Sleep
    mood = db.Column(db.String(50))
    sleep_hours = db.Column(db.Float)
    energy_level = db.Column(db.Integer)     # 1-10

    # Notes
    notes = db.Column(db.Text)
    ai_analysis = db.Column(db.Text)         # AI-generated analysis

    def __repr__(self):
        return f'<HealthRecord {self.recorded_at}>'


class Medication(db.Model):
    """Medication tracking and reminders"""
    __tablename__ = 'medications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))     # once daily, twice daily, etc.
    timing = db.Column(db.String(200))        # morning, afternoon, evening, night
    prescribed_by = db.Column(db.String(150))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    condition_for = db.Column(db.String(200))
    instructions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Medication {self.name}>'


class ChatHistory(db.Model):
    """AI Assistant conversation history"""
    __tablename__ = 'chat_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    agent_type = db.Column(db.String(100))   # which agent handled the query
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatHistory {self.timestamp}>'


class MedicalReport(db.Model):
    """Uploaded medical reports with AI summarization"""
    __tablename__ = 'medical_reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(300))
    original_name = db.Column(db.String(300))
    report_type = db.Column(db.String(100))   # blood test, X-ray, MRI, etc.
    report_date = db.Column(db.Date)
    ai_summary = db.Column(db.Text)
    notes = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MedicalReport {self.original_name}>'
