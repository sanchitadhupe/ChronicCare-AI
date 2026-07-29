"""
Agentic AI Architecture for Chronic Disease Monitoring
Uses IBM watsonx.ai with IBM Granite Foundation Models

AGENT_INSTRUCTIONS:
  - AI behavior: Supportive, evidence-based, empathetic healthcare assistant
  - Response tone: Professional yet warm, clear and easy to understand
  - Safety guidelines: Never diagnose, always recommend professional consultation
  - Medical disclaimer: AI provides general guidance only, not medical advice
  - Personalization: Use patient's health records to tailor responses
  - Chronic disease specialization: Focus on Diabetes, Hypertension, Heart Disease, Asthma, Obesity
  - Indian healthcare: Reference Indian dietary habits, AIIMS/Government hospital guidance
  - Emergency protocol: Immediately direct to emergency services for life-threatening symptoms
  - Language: English with optional regional health context
  - Confidence level: Always indicate uncertainty and recommend verification
"""

import json
import os
import logging
from datetime import datetime
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# AGENT INSTRUCTIONS CONFIGURATION
# Modify these constants to customize AI behavior without changing code logic
# ─────────────────────────────────────────────────────────────────────────────

AGENT_INSTRUCTIONS = {
    "base_persona": (
        "You are HealthGuard AI, an intelligent chronic disease monitoring assistant "
        "powered by IBM Granite. You assist patients in India and worldwide with managing "
        "chronic conditions like Diabetes, Hypertension, Heart Disease, Asthma, and Obesity."
    ),
    "tone": (
        "Be warm, empathetic, professional, and use simple language. "
        "Avoid medical jargon. Speak like a knowledgeable, caring health companion."
    ),
    "safety_guidelines": (
        "NEVER provide a medical diagnosis. NEVER recommend stopping prescribed medications. "
        "ALWAYS recommend consulting a qualified doctor for serious symptoms. "
        "For emergencies (chest pain, stroke symptoms, severe breathing difficulty), "
        "immediately direct the patient to call 112 (India) or visit the nearest emergency room."
    ),
    "disclaimer": (
        "Always end responses with: 'Note: This is AI-generated health guidance and not a substitute "
        "for professional medical advice. Please consult your doctor for personalized medical care.'"
    ),
    "indian_context": (
        "Consider Indian dietary patterns (dal, rice, roti, sabzi), Indian lifestyle factors, "
        "AYUSH recommendations where appropriate, and reference government health schemes like "
        "Ayushman Bharat. Reference normal ranges according to Indian medical standards."
    ),
    "response_format": (
        "Structure responses with clear sections using bullet points. "
        "Keep responses concise but comprehensive. Use emojis sparingly for readability."
    ),
}

AGENT_SPECIALIZATIONS = {
    "PatientProfileAgent": (
        "Analyze patient demographics, medical history, and risk factors. "
        "Provide personalized health baseline assessment."
    ),
    "SymptomAnalysisAgent": (
        "Analyze reported symptoms in context of the patient's chronic conditions. "
        "Identify concerning patterns and suggest when to seek medical attention."
    ),
    "HealthRiskAssessmentAgent": (
        "Calculate and explain health risk scores based on vitals, symptoms, and history. "
        "Categorize risk as Low/Moderate/High/Critical with actionable guidance."
    ),
    "MedicationReminderAgent": (
        "Provide medication adherence tips, general drug interaction awareness (not specific advice), "
        "and reminders. Always recommend pharmacist/doctor for medication questions."
    ),
    "LifestyleRecommendationAgent": (
        "Generate personalized diet, exercise, sleep, and stress management recommendations "
        "tailored to the patient's conditions, Indian dietary preferences, and lifestyle."
    ),
    "HealthReportGeneratorAgent": (
        "Create comprehensive health summaries, trend analyses, and progress reports "
        "from historical health data. Highlight improvements and areas of concern."
    ),
    "EmergencyAlertAgent": (
        "Identify emergency warning signs in health readings or symptoms. "
        "Provide immediate, clear guidance to contact emergency services. "
        "Emergency numbers: 112 (India), 102 (Ambulance), 108 (Emergency Ambulance)."
    ),
}


class WatsonxGraniteClient:
    """IBM watsonx.ai model client — uses chat API (supports Llama & Granite instruct)"""

    def __init__(self):
        self.api_key = os.getenv('IBM_WATSONX_API_KEY')
        self.project_id = os.getenv('IBM_WATSONX_PROJECT_ID')
        self.url = os.getenv('IBM_WATSONX_URL', 'https://au-syd.ml.cloud.ibm.com')
        self.model_id = os.getenv('IBM_GRANITE_MODEL_ID', 'ibm/granite-8b-code-instruct')
        self._model = None

    def get_model(self):
        """Lazy initialization of the model"""
        if self._model is None:
            try:
                credentials = Credentials(
                    url=self.url,
                    api_key=self.api_key
                )
                self._model = ModelInference(
                    model_id=self.model_id,
                    credentials=credentials,
                    project_id=self.project_id,
                )
                logger.info(f"Model initialized: {self.model_id}")
            except Exception as e:
                logger.error(f"Failed to initialize model: {e}")
                raise
        return self._model

    def generate(self, system_text: str, user_text: str) -> str:
        """Generate a response using the chat API"""
        try:
            model = self.get_model()
            messages = [
                {"role": "system", "content": system_text},
                {"role": "user",   "content": user_text},
            ]
            response = model.chat(
                messages=messages,
                params={
                    GenParams.MAX_NEW_TOKENS: 800,
                    GenParams.TEMPERATURE: 0.7,
                    GenParams.TOP_P: 0.9,
                },
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"I'm experiencing technical difficulties. Please try again. Error: {str(e)}"


# Global client instance
_granite_client = None


def get_granite_client() -> WatsonxGraniteClient:
    global _granite_client
    if _granite_client is None:
        _granite_client = WatsonxGraniteClient()
    return _granite_client


def _build_patient_context(patient_profile, recent_records=None) -> str:
    """Build a patient context string for AI prompts"""
    ctx = []
    if patient_profile:
        ctx.append(f"Patient: {patient_profile.full_name or 'Unknown'}, "
                   f"Age: {patient_profile.age or 'N/A'}, "
                   f"Gender: {patient_profile.gender or 'N/A'}")
        if patient_profile.chronic_conditions:
            try:
                conditions = json.loads(patient_profile.chronic_conditions)
                ctx.append(f"Chronic Conditions: {', '.join(conditions)}")
            except Exception:
                ctx.append(f"Chronic Conditions: {patient_profile.chronic_conditions}")
        if patient_profile.bmi:
            ctx.append(f"BMI: {patient_profile.bmi} ({patient_profile.bmi_category})")
        if patient_profile.allergies:
            try:
                allergies = json.loads(patient_profile.allergies)
                if allergies:
                    ctx.append(f"Allergies: {', '.join(allergies)}")
            except Exception:
                pass

    if recent_records:
        latest = recent_records[0] if recent_records else None
        if latest:
            vitals = []
            if latest.blood_pressure_systolic:
                vitals.append(f"BP: {latest.blood_pressure_systolic}/{latest.blood_pressure_diastolic} mmHg")
            if latest.heart_rate:
                vitals.append(f"HR: {latest.heart_rate} bpm")
            if latest.blood_sugar:
                vitals.append(f"Blood Sugar: {latest.blood_sugar} mg/dL ({latest.blood_sugar_type or ''})")
            if latest.oxygen_saturation:
                vitals.append(f"SpO2: {latest.oxygen_saturation}%")
            if vitals:
                ctx.append(f"Latest Vitals ({latest.recorded_at.strftime('%d %b %Y')}): {', '.join(vitals)}")

    return "\n".join(ctx) if ctx else "No patient profile data available."


def _build_system_prompt(agent_name: str, extra_instructions: str = "") -> str:
    """Construct system prompt text for a specific agent"""
    instructions = AGENT_INSTRUCTIONS
    specialization = AGENT_SPECIALIZATIONS.get(agent_name, "")
    parts = [
        instructions['base_persona'],
        f"TONE: {instructions['tone']}",
        f"AGENT ROLE - {agent_name}: {specialization}",
        f"SAFETY: {instructions['safety_guidelines']}",
        f"CONTEXT: {instructions['indian_context']}",
        f"FORMAT: {instructions['response_format']}",
        instructions['disclaimer'],
    ]
    if extra_instructions:
        parts.append(extra_instructions)
    return "\n\n".join(parts)


def _wrap_prompt(system_text: str, user_text: str) -> tuple:
    """Return (system_text, user_text) tuple for the chat API"""
    return system_text, user_text


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIZED AGENTS
# ─────────────────────────────────────────────────────────────────────────────

def patient_profile_agent(patient_profile) -> str:
    """Analyze patient profile and generate health baseline assessment"""
    client = get_granite_client()
    patient_ctx = _build_patient_context(patient_profile)
    system = _build_system_prompt("PatientProfileAgent")
    user_text = f"""Patient Information:
{patient_ctx}

Provide a comprehensive health baseline assessment including:
1. Overview of health status
2. Key risk factors
3. Recommended health monitoring priorities
4. General lifestyle recommendations
5. Questions to discuss with their doctor"""
    return client.generate(*_wrap_prompt(system, user_text))


def symptom_analysis_agent(symptoms: list, severity: int, patient_profile=None, recent_records=None) -> str:
    """Analyze reported symptoms in context of patient history"""
    client = get_granite_client()
    patient_ctx = _build_patient_context(patient_profile, recent_records)
    system = _build_system_prompt("SymptomAnalysisAgent")
    symptoms_str = ", ".join(symptoms) if symptoms else "No specific symptoms reported"
    user_text = f"""Patient Context:
{patient_ctx}

Reported Symptoms: {symptoms_str}
Severity (1-10): {severity}

Analyze these symptoms and provide:
1. Possible explanations given the patient's conditions
2. Severity assessment (mild/moderate/severe/critical)
3. Immediate recommended actions
4. Warning signs to watch for
5. Whether to see a doctor now or wait"""
    return client.generate(*_wrap_prompt(system, user_text))


def health_risk_assessment_agent(patient_profile, recent_records=None) -> str:
    """Comprehensive health risk assessment"""
    client = get_granite_client()
    patient_ctx = _build_patient_context(patient_profile, recent_records)
    system = _build_system_prompt("HealthRiskAssessmentAgent")
    user_text = f"""Patient Data:
{patient_ctx}

Perform a comprehensive health risk assessment including:
1. Overall Risk Level: Low / Moderate / High / Critical
2. Cardiovascular risk assessment
3. Diabetes risk factors
4. Hypertension status analysis
5. Top 3 immediate health concerns
6. Preventive measures recommended
7. Suggested doctor visit frequency"""
    return client.generate(*_wrap_prompt(system, user_text))


def medication_reminder_agent(medications: list, patient_profile=None) -> str:
    """Generate medication adherence guidance and reminders"""
    client = get_granite_client()
    patient_ctx = _build_patient_context(patient_profile)
    system = _build_system_prompt("MedicationReminderAgent")
    med_list = "\n".join([
        f"- {m.get('name', 'Unknown')}: {m.get('dosage', 'N/A')}, "
        f"{m.get('frequency', 'N/A')} ({m.get('timing', 'N/A')})"
        for m in medications
    ]) if medications else "No medications recorded"
    user_text = f"""Patient Context:
{patient_ctx}

Current Medications:
{med_list}

Provide medication adherence guidance including:
1. General tips for remembering medications
2. Best practices for morning, evening, night timing
3. What to do if a dose is missed
4. Food and lifestyle considerations
5. Signs to report to the doctor"""
    return client.generate(*_wrap_prompt(system, user_text))


def lifestyle_recommendation_agent(patient_profile, recent_records=None) -> str:
    """Generate personalized lifestyle recommendations"""
    client = get_granite_client()
    patient_ctx = _build_patient_context(patient_profile, recent_records)
    system = _build_system_prompt("LifestyleRecommendationAgent")
    conditions = []
    if patient_profile and patient_profile.chronic_conditions:
        try:
            conditions = json.loads(patient_profile.chronic_conditions)
        except Exception:
            pass
    user_text = f"""Patient Context:
{patient_ctx}

Create a personalized lifestyle plan including:
1. DIET PLAN: Indian food recommendations for their conditions ({', '.join(conditions) if conditions else 'general'})
2. EXERCISE: Safe activities suitable for their fitness level
3. SLEEP: Optimal sleep routine and tips
4. STRESS MANAGEMENT: Practical relaxation techniques
5. HYDRATION & HABITS: Daily routine recommendations
6. FOODS TO AVOID: Based on their conditions
7. WEEKLY GOALS: 3-5 achievable health goals"""
    return client.generate(*_wrap_prompt(system, user_text))


def health_report_generator_agent(patient_profile, health_records: list, period: str = "weekly") -> str:
    """Generate comprehensive health summary report"""
    client = get_granite_client()
    patient_ctx = _build_patient_context(patient_profile, health_records)
    system = _build_system_prompt("HealthReportGeneratorAgent")

    # Summarize health data
    data_summary = []
    if health_records:
        bp_readings = [(r.blood_pressure_systolic, r.blood_pressure_diastolic)
                       for r in health_records if r.blood_pressure_systolic]
        sugar_readings = [r.blood_sugar for r in health_records if r.blood_sugar]
        hr_readings = [r.heart_rate for r in health_records if r.heart_rate]

        if bp_readings:
            avg_sys = sum(r[0] for r in bp_readings) // len(bp_readings)
            avg_dia = sum(r[1] for r in bp_readings) // len(bp_readings)
            data_summary.append(f"Average BP: {avg_sys}/{avg_dia} mmHg ({len(bp_readings)} readings)")
        if sugar_readings:
            avg_sugar = sum(sugar_readings) / len(sugar_readings)
            data_summary.append(f"Average Blood Sugar: {avg_sugar:.1f} mg/dL ({len(sugar_readings)} readings)")
        if hr_readings:
            avg_hr = sum(hr_readings) // len(hr_readings)
            data_summary.append(f"Average Heart Rate: {avg_hr} bpm")

    data_str = "\n".join(data_summary) if data_summary else "Insufficient data for trend analysis"

    user_text = f"""Patient Context:
{patient_ctx}

Health Data Summary ({period}):
{data_str}
Total Records: {len(health_records)}

Generate a comprehensive {period} health report including:
1. EXECUTIVE SUMMARY: Overall health status
2. VITAL SIGNS ANALYSIS: Trends and observations
3. PROGRESS ASSESSMENT: Improvements or concerns
4. RISK ALERTS: Any concerning patterns
5. RECOMMENDATIONS: Top 5 actions for the next period
6. DOCTOR CONSULTATION: Items to discuss at next appointment"""
    return client.generate(*_wrap_prompt(system, user_text))


def emergency_alert_agent(vitals: dict, symptoms: list) -> dict:
    """Detect emergency conditions and generate appropriate alerts"""
    alerts = []
    risk_level = "normal"

    # Blood pressure checks
    sys_bp = vitals.get('systolic', 0)
    dia_bp = vitals.get('diastolic', 0)
    if sys_bp >= 180 or dia_bp >= 120:
        alerts.append("🚨 HYPERTENSIVE CRISIS: BP extremely high. Call 112 immediately!")
        risk_level = "critical"
    elif sys_bp >= 160 or dia_bp >= 100:
        alerts.append("⚠️ HIGH BLOOD PRESSURE: Seek medical attention today.")
        risk_level = "high"

    # Blood sugar checks
    blood_sugar = vitals.get('blood_sugar', 0)
    if blood_sugar >= 400:
        alerts.append("🚨 SEVERE HYPERGLYCEMIA: Blood sugar dangerously high. Emergency care needed!")
        risk_level = "critical"
    elif blood_sugar >= 250:
        alerts.append("⚠️ HIGH BLOOD SUGAR: Contact your doctor immediately.")
        if risk_level != "critical":
            risk_level = "high"
    elif 0 < blood_sugar < 70:
        alerts.append("🚨 HYPOGLYCEMIA: Blood sugar too low. Take sugar immediately and call doctor!")
        risk_level = "critical"

    # Heart rate checks
    hr = vitals.get('heart_rate', 0)
    if hr > 150 or hr < 40:
        alerts.append("🚨 ABNORMAL HEART RATE: Seek emergency care immediately!")
        risk_level = "critical"

    # SpO2 checks
    spo2 = vitals.get('oxygen_saturation', 100)
    if spo2 < 90:
        alerts.append("🚨 CRITICAL LOW OXYGEN: SpO2 below 90%. Emergency care needed!")
        risk_level = "critical"
    elif spo2 < 95:
        alerts.append("⚠️ LOW OXYGEN SATURATION: Contact doctor immediately.")
        if risk_level != "critical":
            risk_level = "high"

    # Emergency symptoms
    emergency_symptoms = ["chest pain", "difficulty breathing", "stroke", "unconscious",
                          "severe headache", "vision loss", "paralysis", "seizure"]
    if symptoms:
        for symptom in symptoms:
            if any(es in symptom.lower() for es in emergency_symptoms):
                alerts.append(f"🚨 EMERGENCY SYMPTOM DETECTED: '{symptom}'. Call 112 immediately!")
                risk_level = "critical"
                break

    return {
        "risk_level": risk_level,
        "alerts": alerts,
        "emergency_numbers": {"india_emergency": "112", "ambulance": "102/108", "doctor_on_call": "1800-180-1104"},
        "requires_immediate_attention": risk_level == "critical"
    }


def general_health_assistant(user_message: str, patient_profile=None, recent_records=None,
                              chat_history: list = None) -> tuple:
    """General AI health assistant that routes to appropriate specialized agents"""
    client = get_granite_client()
    patient_ctx = _build_patient_context(patient_profile, recent_records)

    # Detect query intent for routing
    msg_lower = user_message.lower()
    if any(word in msg_lower for word in ['diet', 'food', 'eat', 'nutrition', 'exercise', 'lifestyle', 'weight']):
        agent_type = "LifestyleRecommendationAgent"
    elif any(word in msg_lower for word in ['symptom', 'pain', 'feel', 'hurts', 'discomfort', 'fever']):
        agent_type = "SymptomAnalysisAgent"
    elif any(word in msg_lower for word in ['medicine', 'medication', 'tablet', 'drug', 'dose', 'pill']):
        agent_type = "MedicationReminderAgent"
    elif any(word in msg_lower for word in ['risk', 'danger', 'serious', 'concern', 'worry']):
        agent_type = "HealthRiskAssessmentAgent"
    elif any(word in msg_lower for word in ['report', 'summary', 'history', 'trend', 'progress']):
        agent_type = "HealthReportGeneratorAgent"
    elif any(word in msg_lower for word in ['emergency', 'chest pain', 'breathing', 'unconscious', 'stroke']):
        agent_type = "EmergencyAlertAgent"
    else:
        agent_type = "HealthGuardGeneralAgent"

    system = _build_system_prompt(agent_type)

    # Build conversation context from recent history
    history_str = ""
    if chat_history:
        recent = chat_history[-3:]  # Last 3 exchanges
        history_str = "\n".join([
            f"User: {h['message']}\nAssistant: {h['response'][:200]}..."
            for h in recent
        ])

    recent_section = ("Recent Conversation:\n" + history_str) if history_str else ""
    user_text = f"""Patient Context:
{patient_ctx}

{recent_section}

Question: {user_message}"""

    response = client.generate(*_wrap_prompt(system, user_text))
    return response, agent_type


def summarize_medical_report(report_text: str, report_type: str = "medical report") -> str:
    """Summarize uploaded medical report using AI"""
    client = get_granite_client()
    system_text = (
        "You are a medical report interpreter. Provide patient-friendly summaries. "
        "Never diagnose. Always recommend discussing results with a doctor."
    )
    user_text = f"""A patient uploaded a {report_type}. Provide a patient-friendly summary:
1. Explain key findings in simple language
2. Highlight any abnormal values without causing alarm
3. Suggest questions to ask the doctor
4. Note any urgent findings needing immediate attention

Report Content:
{report_text[:3000]}"""
    return client.generate(*_wrap_prompt(system_text, user_text))
