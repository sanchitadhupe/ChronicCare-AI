"""Dashboard routes for Chronic Disease Monitoring"""
import json
import os
import uuid
import logging
from datetime import datetime, date
from werkzeug.utils import secure_filename

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app
)
from flask_login import login_required, current_user

from models import (
    db, PatientProfile, HealthRecord, Medication,
    ChatHistory, MedicalReport
)
from forms import (
    PatientProfileForm, HealthRecordForm,
    MedicationForm, MedicalReportUploadForm
)
import agents

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD HOME
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()
    recent_records = (
        HealthRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(HealthRecord.recorded_at.desc())
        .limit(7).all()
    )
    medications = (
        Medication.query
        .filter_by(user_id=current_user.id, is_active=True)
        .order_by(Medication.name).all()
    )
    latest = recent_records[0] if recent_records else None

    # Alert check
    emergency_info = None
    if latest:
        vitals = {
            'systolic': latest.blood_pressure_systolic or 0,
            'diastolic': latest.blood_pressure_diastolic or 0,
            'blood_sugar': latest.blood_sugar or 0,
            'heart_rate': latest.heart_rate or 0,
            'oxygen_saturation': latest.oxygen_saturation or 100,
        }
        symptoms = []
        if latest.symptoms:
            try:
                symptoms = json.loads(latest.symptoms)
            except Exception:
                pass
        emergency_info = agents.emergency_alert_agent(vitals, symptoms)

    # Chart data (last 7 readings)
    chart_data = {
        'labels': [],
        'bp_sys': [], 'bp_dia': [],
        'sugar': [], 'heart_rate': [],
    }
    for r in reversed(recent_records):
        chart_data['labels'].append(r.recorded_at.strftime('%d %b'))
        chart_data['bp_sys'].append(r.blood_pressure_systolic)
        chart_data['bp_dia'].append(r.blood_pressure_diastolic)
        chart_data['sugar'].append(r.blood_sugar)
        chart_data['heart_rate'].append(r.heart_rate)

    return render_template('dashboard/index.html',
                           profile=profile,
                           latest=latest,
                           medications=medications,
                           emergency_info=emergency_info,
                           chart_data=chart_data,
                           record_count=len(recent_records))


# ─────────────────────────────────────────────────────────────────────────────
# PATIENT PROFILE
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()
    form = PatientProfileForm(obj=profile)

    if form.validate_on_submit():
        if not profile:
            profile = PatientProfile(user_id=current_user.id)
            db.session.add(profile)

        form.populate_obj(profile)

        # Handle multi-select fields (chronic conditions)
        profile.chronic_conditions = json.dumps(form.chronic_conditions.data)

        # Handle allergies as JSON
        allergies_text = form.allergies.data or ''
        allergy_list = [a.strip() for a in allergies_text.split('\n') if a.strip()]
        profile.allergies = json.dumps(allergy_list)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard.profile'))

    # Pre-populate multi-fields
    if profile and profile.chronic_conditions:
        try:
            form.chronic_conditions.data = json.loads(profile.chronic_conditions)
        except Exception:
            pass
    if profile and profile.allergies:
        try:
            allergy_list = json.loads(profile.allergies)
            form.allergies.data = '\n'.join(allergy_list)
        except Exception:
            pass

    return render_template('dashboard/profile.html', form=form, profile=profile)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH MONITORING
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/health-monitor', methods=['GET', 'POST'])
@login_required
def health_monitor():
    form = HealthRecordForm()
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()

    if form.validate_on_submit():
        record = HealthRecord(user_id=current_user.id)
        form.populate_obj(record)
        record.symptoms = json.dumps(form.symptoms.data)

        db.session.add(record)
        db.session.commit()
        flash('Health record saved successfully!', 'success')
        return redirect(url_for('dashboard.health_history'))

    records = (HealthRecord.query.filter_by(user_id=current_user.id)
               .order_by(HealthRecord.recorded_at.desc()).limit(10).all())

    return render_template('dashboard/health_monitor.html',
                           form=form, records=records, profile=profile)


@dashboard_bp.route('/health-history')
@login_required
def health_history():
    page = request.args.get('page', 1, type=int)
    records = (HealthRecord.query.filter_by(user_id=current_user.id)
               .order_by(HealthRecord.recorded_at.desc())
               .paginate(page=page, per_page=15, error_out=False))

    # Chart data for last 30 records
    all_records = (HealthRecord.query.filter_by(user_id=current_user.id)
                   .order_by(HealthRecord.recorded_at.asc()).limit(30).all())
    chart_data = {
        'labels': [r.recorded_at.strftime('%d %b') for r in all_records],
        'bp_sys': [r.blood_pressure_systolic for r in all_records],
        'bp_dia': [r.blood_pressure_diastolic for r in all_records],
        'sugar': [r.blood_sugar for r in all_records],
        'heart_rate': [r.heart_rate for r in all_records],
        'spo2': [r.oxygen_saturation for r in all_records],
    }
    return render_template('dashboard/health_history.html',
                           records=records, chart_data=chart_data)


# ─────────────────────────────────────────────────────────────────────────────
# MEDICATIONS
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/medications', methods=['GET', 'POST'])
@login_required
def medications():
    form = MedicationForm()
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()

    if form.validate_on_submit():
        med = Medication(user_id=current_user.id)
        form.populate_obj(med)
        db.session.add(med)
        db.session.commit()
        flash(f'Medication "{med.name}" added successfully!', 'success')
        return redirect(url_for('dashboard.medications'))

    meds = (Medication.query.filter_by(user_id=current_user.id)
            .order_by(Medication.is_active.desc(), Medication.name).all())

    return render_template('dashboard/medications.html',
                           form=form, medications=meds, profile=profile)


@dashboard_bp.route('/medications/<int:med_id>/toggle', methods=['POST'])
@login_required
def toggle_medication(med_id):
    med = Medication.query.filter_by(id=med_id, user_id=current_user.id).first_or_404()
    med.is_active = not med.is_active
    db.session.commit()
    status = 'activated' if med.is_active else 'deactivated'
    flash(f'Medication {status}.', 'info')
    return redirect(url_for('dashboard.medications'))


@dashboard_bp.route('/medications/<int:med_id>/delete', methods=['POST'])
@login_required
def delete_medication(med_id):
    med = Medication.query.filter_by(id=med_id, user_id=current_user.id).first_or_404()
    db.session.delete(med)
    db.session.commit()
    flash('Medication removed.', 'info')
    return redirect(url_for('dashboard.medications'))


# ─────────────────────────────────────────────────────────────────────────────
# AI HEALTH ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH REPORTS
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/reports')
@login_required
def reports():
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()
    period = request.args.get('period', 'weekly')
    limit_map = {'weekly': 7, 'monthly': 30, 'quarterly': 90}
    limit = limit_map.get(period, 7)

    records = (HealthRecord.query.filter_by(user_id=current_user.id)
               .order_by(HealthRecord.recorded_at.desc()).limit(limit).all())

    return render_template('dashboard/reports.html',
                           profile=profile, records=records, period=period)


# ─────────────────────────────────────────────────────────────────────────────
# MEDICAL REPORT UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/medical-reports', methods=['GET', 'POST'])
@login_required
def medical_reports():
    form = MedicalReportUploadForm()
    if form.validate_on_submit():
        file = form.report_file.data
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{current_user.id}_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            report = MedicalReport(
                user_id=current_user.id,
                filename=filename,
                original_name=secure_filename(file.filename),
                report_type=form.report_type.data,
                report_date=form.report_date.data,
                notes=form.notes.data,
            )

            db.session.add(report)
            db.session.commit()
            flash('Medical report uploaded successfully!', 'success')
            return redirect(url_for('dashboard.medical_reports'))
        else:
            flash('Invalid file type. Please upload PDF, JPG, or PNG.', 'danger')

    reports_list = (MedicalReport.query.filter_by(user_id=current_user.id)
                    .order_by(MedicalReport.uploaded_at.desc()).all())

    return render_template('dashboard/medical_reports.html',
                           form=form, reports=reports_list)


@dashboard_bp.route('/medical-reports/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    report = MedicalReport.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], report.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(report)
    db.session.commit()
    flash('Report deleted.', 'info')
    return redirect(url_for('dashboard.medical_reports'))


# ─────────────────────────────────────────────────────────────────────────────
# BMI CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/bmi-calculator')
@login_required
def bmi_calculator():
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('dashboard/bmi_calculator.html', profile=profile)


# ─────────────────────────────────────────────────────────────────────────────
# RISK ASSESSMENT
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/risk-assessment')
@login_required
def risk_assessment():
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()
    recent_records = (HealthRecord.query.filter_by(user_id=current_user.id)
                      .order_by(HealthRecord.recorded_at.desc()).limit(10).all())

    return render_template('dashboard/risk_assessment.html',
                           profile=profile,
                           recent_records=recent_records)


# ─────────────────────────────────────────────────────────────────────────────
# AI HEALTH ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/ai-assistant')
@login_required
def ai_assistant():
    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()
    chat_history = (
        ChatHistory.query.filter_by(user_id=current_user.id)
        .order_by(ChatHistory.timestamp.asc()).limit(50).all()
    )
    return render_template('dashboard/ai_assistant.html',
                           profile=profile, chat_history=chat_history)
