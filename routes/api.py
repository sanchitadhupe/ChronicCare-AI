"""API routes for AJAX calls"""
import json
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db, HealthRecord, PatientProfile, Medication, ChatHistory
import agents       # emergency_alert_agent is pure Python — no IBM Watson call
import chatbot      # rule-based chatbot — no external API

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)


@api_bp.route('/health-data', methods=['GET'])
@login_required
def health_data():
    """Get health chart data as JSON"""
    limit = request.args.get('limit', 30, type=int)
    records = (
        HealthRecord.query.filter_by(user_id=current_user.id)
        .order_by(HealthRecord.recorded_at.asc())
        .limit(limit).all()
    )
    return jsonify({
        'labels': [r.recorded_at.strftime('%d %b %Y') for r in records],
        'bp_systolic': [r.blood_pressure_systolic for r in records],
        'bp_diastolic': [r.blood_pressure_diastolic for r in records],
        'heart_rate': [r.heart_rate for r in records],
        'blood_sugar': [r.blood_sugar for r in records],
        'spo2': [r.oxygen_saturation for r in records],
        'weight': [r.weight_kg for r in records],
    })


@api_bp.route('/emergency-check', methods=['POST'])
@login_required
def emergency_check():
    """Check vitals for emergency conditions"""
    data = request.get_json() or {}
    vitals = {
        'systolic': data.get('systolic', 0),
        'diastolic': data.get('diastolic', 0),
        'blood_sugar': data.get('blood_sugar', 0),
        'heart_rate': data.get('heart_rate', 0),
        'oxygen_saturation': data.get('oxygen_saturation', 100),
    }
    symptoms = data.get('symptoms', [])
    result = agents.emergency_alert_agent(vitals, symptoms)
    return jsonify(result)


@api_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    """Get dashboard statistics"""
    total_records = HealthRecord.query.filter_by(user_id=current_user.id).count()
    active_meds = Medication.query.filter_by(user_id=current_user.id, is_active=True).count()
    latest = (HealthRecord.query.filter_by(user_id=current_user.id)
              .order_by(HealthRecord.recorded_at.desc()).first())

    return jsonify({
        'total_records': total_records,
        'active_medications': active_meds,
        'last_recorded': latest.recorded_at.isoformat() if latest else None,
        'bp_status': _classify_bp(latest) if latest else 'unknown',
        'sugar_status': _classify_sugar(latest) if latest else 'unknown',
    })


def _classify_bp(record):
    if not record or not record.blood_pressure_systolic:
        return 'unknown'
    sys = record.blood_pressure_systolic
    dia = record.blood_pressure_diastolic or 0
    if sys >= 180 or dia >= 120:
        return 'critical'
    elif sys >= 140 or dia >= 90:
        return 'high'
    elif sys >= 130 or dia >= 80:
        return 'elevated'
    elif sys >= 120:
        return 'normal_high'
    else:
        return 'normal'


def _classify_sugar(record):
    if not record or not record.blood_sugar:
        return 'unknown'
    sugar = record.blood_sugar
    if sugar < 70:
        return 'low'
    elif sugar <= 100:
        return 'normal'
    elif sugar <= 125:
        return 'prediabetes'
    elif sugar <= 200:
        return 'high'
    else:
        return 'very_high'


@api_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Rule-based health assistant — no external API required"""
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    profile = PatientProfile.query.filter_by(user_id=current_user.id).first()
    latest_record = (
        HealthRecord.query.filter_by(user_id=current_user.id)
        .order_by(HealthRecord.recorded_at.desc()).first()
    )
    from models import Medication as Med
    medications = (
        Med.query.filter_by(user_id=current_user.id, is_active=True)
        .order_by(Med.name).all()
    )

    response, agent_type = chatbot.get_response(message, profile, latest_record, medications)

    # Save to chat history
    try:
        entry = ChatHistory(
            user_id=current_user.id,
            message=message,
            response=response,
            agent_type=agent_type,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")

    return jsonify({'response': response, 'agent_type': agent_type})
