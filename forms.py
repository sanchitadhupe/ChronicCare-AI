"""
Flask-WTF Forms for Chronic Disease Monitoring Application
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, IntegerField, FloatField, TextAreaField,
    SelectField, SelectMultipleField, DateField, BooleanField, HiddenField,
    SubmitField, widgets
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional,
    NumberRange, ValidationError
)


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


CHRONIC_CONDITIONS = [
    ('diabetes_type1', 'Type 1 Diabetes'),
    ('diabetes_type2', 'Type 2 Diabetes'),
    ('hypertension', 'Hypertension (High BP)'),
    ('heart_disease', 'Heart Disease'),
    ('asthma', 'Asthma'),
    ('copd', 'COPD'),
    ('obesity', 'Obesity'),
    ('thyroid', 'Thyroid Disorder'),
    ('kidney_disease', 'Chronic Kidney Disease'),
    ('arthritis', 'Arthritis'),
    ('depression', 'Depression/Anxiety'),
    ('cancer', 'Cancer (specify in notes)'),
]

SYMPTOM_CHOICES = [
    ('headache', 'Headache'),
    ('fatigue', 'Fatigue/Tiredness'),
    ('chest_pain', 'Chest Pain'),
    ('shortness_breath', 'Shortness of Breath'),
    ('dizziness', 'Dizziness'),
    ('nausea', 'Nausea/Vomiting'),
    ('back_pain', 'Back Pain'),
    ('joint_pain', 'Joint Pain'),
    ('swelling', 'Swelling in Feet/Hands'),
    ('vision_blur', 'Blurred Vision'),
    ('increased_thirst', 'Increased Thirst'),
    ('frequent_urination', 'Frequent Urination'),
    ('numbness', 'Numbness/Tingling'),
    ('palpitations', 'Heart Palpitations'),
    ('anxiety', 'Anxiety/Stress'),
    ('insomnia', 'Insomnia/Sleep Issues'),
    ('fever', 'Fever'),
    ('cough', 'Cough'),
]


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class PatientProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=150)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')
    ], validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[
        ('', 'Select'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')
    ], validators=[Optional()])
    height_cm = FloatField('Height (cm)', validators=[Optional(), NumberRange(min=50, max=250)])
    weight_kg = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=10, max=500)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    emergency_contact = StringField('Emergency Contact Name', validators=[Optional(), Length(max=150)])
    emergency_phone = StringField('Emergency Contact Phone', validators=[Optional(), Length(max=20)])

    chronic_conditions = MultiCheckboxField('Chronic Conditions', choices=CHRONIC_CONDITIONS)
    allergies = TextAreaField('Allergies (one per line)', validators=[Optional()])
    family_history = TextAreaField('Family Medical History', validators=[Optional()])

    smoking_status = SelectField('Smoking Status', choices=[
        ('never', 'Never Smoked'), ('former', 'Former Smoker'), ('current', 'Current Smoker')
    ], validators=[Optional()])
    alcohol_consumption = SelectField('Alcohol Consumption', choices=[
        ('none', 'None'), ('occasional', 'Occasional'), ('moderate', 'Moderate'), ('heavy', 'Heavy')
    ], validators=[Optional()])
    physical_activity = SelectField('Physical Activity Level', choices=[
        ('sedentary', 'Sedentary'), ('light', 'Light (1-2 days/week)'),
        ('moderate', 'Moderate (3-5 days/week)'), ('active', 'Active (6-7 days/week)')
    ], validators=[Optional()])
    diet_type = SelectField('Diet Type', choices=[
        ('omnivore', 'Omnivore'), ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'), ('jain', 'Jain'), ('other', 'Other')
    ], validators=[Optional()])

    primary_doctor = StringField('Primary Doctor Name', validators=[Optional(), Length(max=150)])
    doctor_phone = StringField('Doctor Phone', validators=[Optional(), Length(max=20)])
    hospital = StringField('Hospital/Clinic', validators=[Optional(), Length(max=200)])

    submit = SubmitField('Save Profile')


class HealthRecordForm(FlaskForm):
    blood_pressure_systolic = IntegerField('Systolic BP (mmHg)', validators=[Optional(), NumberRange(min=60, max=300)])
    blood_pressure_diastolic = IntegerField('Diastolic BP (mmHg)', validators=[Optional(), NumberRange(min=40, max=200)])
    heart_rate = IntegerField('Heart Rate (bpm)', validators=[Optional(), NumberRange(min=30, max=300)])
    blood_sugar = FloatField('Blood Sugar (mg/dL)', validators=[Optional(), NumberRange(min=20, max=800)])
    blood_sugar_type = SelectField('Reading Type', choices=[
        ('fasting', 'Fasting'), ('post_meal', 'Post-Meal (2hr)'), ('random', 'Random'), ('hba1c', 'HbA1c')
    ], validators=[Optional()])
    temperature = FloatField('Temperature (°C)', validators=[Optional(), NumberRange(min=34, max=45)])
    oxygen_saturation = FloatField('SpO2 (%)', validators=[Optional(), NumberRange(min=50, max=100)])
    weight_kg = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=10, max=500)])
    symptoms = MultiCheckboxField('Symptoms', choices=SYMPTOM_CHOICES)
    symptom_severity = IntegerField('Overall Severity (1-10)', validators=[Optional(), NumberRange(min=1, max=10)])
    pain_level = IntegerField('Pain Level (0-10)', validators=[Optional(), NumberRange(min=0, max=10)])
    mood = SelectField('Mood', choices=[
        ('excellent', 'Excellent 😊'), ('good', 'Good 🙂'), ('fair', 'Fair 😐'),
        ('poor', 'Poor 😔'), ('very_poor', 'Very Poor 😢')
    ], validators=[Optional()])
    sleep_hours = FloatField('Sleep Hours', validators=[Optional(), NumberRange(min=0, max=24)])
    energy_level = IntegerField('Energy Level (1-10)', validators=[Optional(), NumberRange(min=1, max=10)])
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    submit = SubmitField('Save Health Record')


class MedicationForm(FlaskForm):
    name = StringField('Medication Name', validators=[DataRequired(), Length(max=200)])
    dosage = StringField('Dosage', validators=[Optional(), Length(max=100)])
    frequency = SelectField('Frequency', choices=[
        ('once_daily', 'Once Daily'), ('twice_daily', 'Twice Daily'),
        ('three_times', 'Three Times Daily'), ('four_times', 'Four Times Daily'),
        ('weekly', 'Weekly'), ('as_needed', 'As Needed'), ('other', 'Other')
    ], validators=[Optional()])
    timing = StringField('Timing (e.g., Morning, Night)', validators=[Optional(), Length(max=200)])
    prescribed_by = StringField('Prescribed By', validators=[Optional(), Length(max=150)])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    condition_for = StringField('For Condition', validators=[Optional(), Length(max=200)])
    instructions = TextAreaField('Special Instructions', validators=[Optional()])
    submit = SubmitField('Save Medication')


class MedicalReportUploadForm(FlaskForm):
    report_file = FileField('Upload Report', validators=[
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF and image files allowed!')
    ])
    report_type = SelectField('Report Type', choices=[
        ('blood_test', 'Blood Test'), ('urine_test', 'Urine Test'),
        ('ecg', 'ECG/EKG'), ('xray', 'X-Ray'), ('mri', 'MRI'),
        ('ultrasound', 'Ultrasound'), ('ct_scan', 'CT Scan'),
        ('prescription', 'Prescription'), ('discharge_summary', 'Discharge Summary'),
        ('other', 'Other')
    ])
    report_date = DateField('Report Date', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Upload & Analyze')
