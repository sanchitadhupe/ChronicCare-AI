"""
Rule-based Health Chatbot — no external API required.
Answers health questions using the patient's own stored data.
"""
import json
import re
from datetime import datetime


# ── Keyword routing ────────────────────────────────────────────────────────

_DIET = ['diet', 'food', 'eat', 'nutrition', 'meal', 'breakfast', 'lunch', 'dinner',
         'vegetable', 'fruit', 'sugar', 'salt', 'fat', 'carb', 'protein', 'calorie']
_EXERCISE = ['exercise', 'workout', 'walk', 'run', 'gym', 'yoga', 'activity', 'fitness',
             'physical', 'sport', 'swim', 'cycling']
_MEDICATION = ['medicine', 'medication', 'tablet', 'drug', 'dose', 'pill', 'capsule',
               'dosage', 'prescription', 'miss', 'forgot', 'reminder']
_SYMPTOM = ['symptom', 'pain', 'feel', 'ache', 'hurt', 'discomfort', 'fever',
            'headache', 'dizzy', 'fatigue', 'tired', 'nausea', 'vomit', 'cough',
            'breathe', 'sweat', 'blurred', 'chest', 'weak']
_BP = ['blood pressure', 'bp', 'hypertension', 'systolic', 'diastolic', 'mmhg',
       'pressure', 'hyper', 'hypo']
_SUGAR = ['blood sugar', 'glucose', 'diabetes', 'diabetic', 'insulin', 'hba1c',
          'fasting', 'post meal', 'hyperglycemia', 'hypoglycemia']
_RISK = ['risk', 'danger', 'serious', 'concern', 'worried', 'critical', 'safe', 'assessment']
_VITALS = ['vitals', 'reading', 'record', 'last reading', 'recent', 'my health',
           'my data', 'how am i', 'status']
_EMERGENCY = ['emergency', 'urgent', 'call', '112', 'ambulance', 'hospital',
              'unconscious', 'stroke', 'attack']
_SLEEP = ['sleep', 'insomnia', 'rest', 'tired', 'fatigue', 'energy']
_STRESS = ['stress', 'anxiety', 'mental', 'depression', 'mood', 'relax', 'calm']
_WEIGHT = ['weight', 'bmi', 'obese', 'overweight', 'underweight', 'fat', 'slim', 'lose weight']
_GREETING = ['hello', 'hi', 'hey', 'help', 'start', 'good morning', 'good evening',
             'good afternoon', 'what can you do', 'who are you']


def _match(msg, keywords):
    m = msg.lower()
    return any(k in m for k in keywords)


# ── Context builders ───────────────────────────────────────────────────────

def _fmt_conditions(profile):
    if not profile or not profile.chronic_conditions:
        return None
    try:
        conds = json.loads(profile.chronic_conditions)
        return ', '.join(c.replace('_', ' ').title() for c in conds) if conds else None
    except Exception:
        return None


def _fmt_vitals(record):
    if not record:
        return None
    parts = []
    if record.blood_pressure_systolic:
        parts.append(f"BP {record.blood_pressure_systolic}/{record.blood_pressure_diastolic} mmHg")
    if record.heart_rate:
        parts.append(f"Heart Rate {record.heart_rate} bpm")
    if record.blood_sugar:
        parts.append(f"Blood Sugar {record.blood_sugar} mg/dL")
    if record.oxygen_saturation:
        parts.append(f"SpO₂ {record.oxygen_saturation}%")
    if record.weight_kg:
        parts.append(f"Weight {record.weight_kg} kg")
    return ', '.join(parts) if parts else None


# ── Response generators ────────────────────────────────────────────────────

def _greeting(profile, latest):
    name = (profile.full_name or '').split()[0] if profile and profile.full_name else 'there'
    conds = _fmt_conditions(profile)
    cond_line = f"\n\nI can see you're managing **{conds}**. I'll keep that in mind for all my answers." if conds else ""
    return (
        f"Hello {name}! 👋 I'm **HealthGuard**, your personal health assistant.{cond_line}\n\n"
        "I can help you with:\n"
        "• 🩺 Your symptoms & what they may mean\n"
        "• 💊 Medication tips & reminders\n"
        "• 🥗 Diet & nutrition guidance\n"
        "• 🏃 Exercise recommendations\n"
        "• 📊 Your latest vitals & risk status\n"
        "• 😴 Sleep & stress tips\n\n"
        "What would you like to know today?"
    )


def _vitals_summary(profile, latest):
    if not latest:
        return (
            "I don't have any recorded vitals for you yet.\n\n"
            "👉 Go to **Log Vitals** to record your blood pressure, blood sugar, heart rate, and more. "
            "Once you have records, I can give you a full health status update."
        )
    v = _fmt_vitals(latest)
    date_str = latest.recorded_at.strftime('%d %b %Y at %H:%M')
    alerts = []

    if latest.blood_pressure_systolic:
        s = latest.blood_pressure_systolic
        if s >= 180:
            alerts.append("🚨 **Blood pressure is critically high** — seek emergency care immediately (call 112).")
        elif s >= 140:
            alerts.append("⚠️ **Blood pressure is high** — contact your doctor today.")
        elif s >= 130:
            alerts.append("⚠️ Blood pressure is slightly elevated. Monitor closely.")

    if latest.blood_sugar:
        sg = latest.blood_sugar
        if sg >= 400:
            alerts.append("🚨 **Blood sugar is dangerously high** — go to emergency immediately.")
        elif sg >= 200:
            alerts.append("⚠️ **Blood sugar is high** — contact your doctor.")
        elif sg < 70:
            alerts.append("🚨 **Blood sugar is too low** — take sugar/glucose immediately.")

    if latest.oxygen_saturation and latest.oxygen_saturation < 92:
        alerts.append("🚨 **Oxygen saturation is critically low** — seek immediate medical help.")

    alert_block = ('\n\n**Alerts:**\n' + '\n'.join(alerts)) if alerts else '\n\n✅ No critical alerts in your latest reading.'
    bmi_line = f"\n\n**BMI:** {profile.bmi} ({profile.bmi_category})" if profile and profile.bmi else ''

    return (
        f"📊 **Your Latest Vitals** (recorded {date_str})\n\n"
        f"{v or 'No vital values recorded.'}"
        f"{bmi_line}"
        f"{alert_block}"
    )


def _bp_advice(profile, latest):
    conds = _fmt_conditions(profile)
    base = (
        "**Blood Pressure Tips:**\n\n"
        "• Normal range: 90–120 / 60–80 mmHg\n"
        "• Elevated: 120–129 systolic\n"
        "• High (Stage 1): 130–139 / 80–89\n"
        "• High (Stage 2): 140+ / 90+\n"
        "• Crisis: 180+ / 120+ → **call 112 immediately**\n\n"
        "**To lower blood pressure:**\n"
        "• Reduce salt intake (less than 5g/day)\n"
        "• Eat potassium-rich foods: banana, spinach, dal, coconut water\n"
        "• Avoid pickles, papad, processed foods\n"
        "• Walk 30 minutes daily\n"
        "• Manage stress with deep breathing or meditation\n"
        "• Limit alcohol and quit smoking\n"
        "• Take prescribed medications consistently"
    )
    if latest and latest.blood_pressure_systolic and latest.blood_pressure_systolic >= 140:
        base += f"\n\n⚠️ Your last recorded BP was {latest.blood_pressure_systolic}/{latest.blood_pressure_diastolic} mmHg — please consult your doctor."
    return base


def _sugar_advice(profile, latest):
    base = (
        "**Blood Sugar / Diabetes Tips:**\n\n"
        "• Fasting normal: 70–100 mg/dL\n"
        "• Post-meal normal: below 140 mg/dL\n"
        "• Pre-diabetes (fasting): 100–125 mg/dL\n"
        "• Diabetes (fasting): 126+ mg/dL\n\n"
        "**To manage blood sugar:**\n"
        "• Eat small, frequent meals (every 3–4 hours)\n"
        "• Choose low glycemic foods: oats, brown rice, vegetables, dal\n"
        "• Avoid: white rice in large quantity, maida, sugary drinks, sweets\n"
        "• Walk after meals (even 10–15 minutes helps)\n"
        "• Monitor regularly — morning fasting and 2 hours after meals\n"
        "• Never skip prescribed diabetes medications\n"
        "• Keep glucose tablets/candy handy for low sugar episodes"
    )
    if latest and latest.blood_sugar and latest.blood_sugar >= 200:
        base += f"\n\n⚠️ Your last recorded blood sugar was {latest.blood_sugar} mg/dL — please contact your doctor."
    return base


def _diet_advice(profile):
    conds = _fmt_conditions(profile)
    base = "**Diet & Nutrition Tips:**\n\n"
    if conds:
        base += f"Personalised for your conditions: **{conds}**\n\n"
    base += (
        "• 🥣 **Breakfast:** Oats/poha/upma + fruit + low-fat milk or curd\n"
        "• 🍱 **Lunch:** 2 roti + dal + sabzi + salad + curd\n"
        "• 🥗 **Snack:** Handful of nuts, fruit, or sprouts\n"
        "• 🌙 **Dinner:** Light — soup + 1 roti + sabzi (avoid heavy carbs)\n\n"
        "**Foods to include:**\n"
        "• Leafy greens (palak, methi), bitter gourd (karela), amla\n"
        "• Whole grains: brown rice, jowar, bajra, ragi\n"
        "• Protein: moong dal, chana, eggs, fish (2×/week)\n\n"
        "**Foods to limit:**\n"
        "• Fried snacks, bakery items, processed foods\n"
        "• Excess salt, sugar, ghee in large quantities\n"
        "• Sugary beverages — replace with nimbu pani without sugar\n\n"
        "• Drink 8–10 glasses of water daily"
    )
    return base


def _exercise_advice(profile):
    conds = _fmt_conditions(profile)
    base = "**Exercise Recommendations:**\n\n"
    if conds:
        base += f"Tailored for: **{conds}**\n\n"
    base += (
        "• 🚶 **Walking:** 30–45 minutes daily, brisk pace\n"
        "• 🧘 **Yoga:** Pranayama and gentle asanas — excellent for BP and diabetes\n"
        "• 🚴 **Cycling / Swimming:** Low-impact, great for joints\n"
        "• 💪 **Strength training:** 2×/week with light weights\n\n"
        "**Tips:**\n"
        "• Always warm up for 5 minutes before exercise\n"
        "• If you have diabetes, carry glucose in case of low sugar\n"
        "• Avoid intense exercise if BP is above 160/100\n"
        "• Start slow — even 10 minutes 3× daily is effective\n"
        "• Consistency beats intensity — daily 30 min walk is better than 2-hour gym once a week"
    )
    return base


def _medication_advice(meds):
    base = "**Medication Tips:**\n\n"
    if meds:
        base += "**Your current medications:**\n"
        for m in meds[:6]:
            base += f"• {m.name} — {m.dosage or 'dosage N/A'}, {m.frequency or 'frequency N/A'}"
            if m.timing:
                base += f" ({m.timing})"
            base += "\n"
        base += "\n"
    base += (
        "**General reminders:**\n"
        "• Take medications at the same time every day\n"
        "• Use a pill organiser or phone alarm\n"
        "• Never stop medication without consulting your doctor\n"
        "• If you miss a dose, take it as soon as you remember (unless it's almost time for the next)\n"
        "• Keep a list of all medications in your wallet for emergencies\n"
        "• Store medicines in a cool, dry place away from sunlight"
    )
    return base


def _sleep_advice():
    return (
        "**Sleep & Rest Tips:**\n\n"
        "• Aim for 7–8 hours of quality sleep each night\n"
        "• Sleep and wake at the same time daily — even on weekends\n"
        "• Avoid screens (phone/TV) 30 minutes before bed\n"
        "• Keep the room dark, cool, and quiet\n"
        "• Avoid heavy meals or caffeine after 7 PM\n"
        "• A short 15–20 min afternoon nap is acceptable\n"
        "• If sleep is consistently poor, discuss with your doctor — poor sleep worsens BP, sugar, and heart health"
    )


def _stress_advice():
    return (
        "**Stress & Mental Wellbeing Tips:**\n\n"
        "• **Deep breathing:** 4-7-8 technique — inhale 4s, hold 7s, exhale 8s (repeat 3×)\n"
        "• **Meditation:** Even 10 minutes of mindfulness daily reduces cortisol\n"
        "• **Yoga & Pranayama:** Anulom Vilom, Bhramari are highly effective\n"
        "• **Physical activity:** Walking and exercise are natural stress-busters\n"
        "• **Social connection:** Talk to family, friends, or a counsellor\n"
        "• **Hobbies:** Read, garden, cook, listen to music\n"
        "• Chronic stress raises blood pressure and blood sugar — managing it is as important as medication"
    )


def _weight_advice(profile):
    bmi_line = ""
    if profile and profile.bmi:
        bmi_line = f"Your current BMI is **{profile.bmi}** ({profile.bmi_category}).\n\n"
    return (
        f"**Weight Management:**\n\n{bmi_line}"
        "• BMI under 18.5 → Underweight | 18.5–24.9 → Normal | 25–29.9 → Overweight | 30+ → Obese\n\n"
        "**To manage weight:**\n"
        "• No crash dieting — aim for 0.5 kg loss per week\n"
        "• Eat smaller portions, use a smaller plate\n"
        "• Replace refined carbs with whole grains\n"
        "• Walk at least 45 minutes daily\n"
        "• Drink a glass of water before each meal\n"
        "• Track what you eat — even mentally — it increases awareness\n"
        "• Consult a dietitian for a personalised meal plan"
    )


def _symptom_advice(msg):
    advice = "**Regarding your symptoms:**\n\n"
    advice += "I'm not a doctor and cannot diagnose. However:\n\n"
    if 'chest' in msg.lower():
        advice += "🚨 **Chest pain or tightness can be serious.** If you have chest pain, shortness of breath, or pain radiating to your arm/jaw — **call 112 immediately.**\n\n"
    if 'dizzy' in msg.lower() or 'dizziness' in msg.lower():
        advice += "⚠️ Dizziness can be caused by low blood sugar, low BP, or dehydration. Check your BP/sugar, drink water, and sit down safely.\n\n"
    if 'headache' in msg.lower():
        advice += "⚠️ Headaches with high BP are common. Check your BP. If it's above 180, seek immediate care.\n\n"
    advice += (
        "**General guidance:**\n"
        "• Note when the symptom started, how often, and severity (1-10)\n"
        "• Log your symptoms in **Log Vitals** so your doctor can review\n"
        "• For any symptom lasting more than 2 days or getting worse — consult your doctor\n"
        "• **Emergency: Call 112 | Ambulance: 102 / 108**"
    )
    return advice


def _emergency_info():
    return (
        "🚨 **Emergency Information:**\n\n"
        "**India Emergency Numbers:**\n"
        "• **112** — National Emergency (Police, Fire, Ambulance)\n"
        "• **102** — Ambulance\n"
        "• **108** — Emergency Ambulance Service\n"
        "• **1800-180-1104** — Health helpline\n\n"
        "**When to call 112 immediately:**\n"
        "• Chest pain or pressure\n"
        "• Sudden severe headache\n"
        "• Difficulty breathing\n"
        "• Signs of stroke (face drooping, arm weakness, speech difficulty)\n"
        "• Blood sugar below 50 or above 400 mg/dL\n"
        "• Blood pressure above 180/120 mmHg\n"
        "• Loss of consciousness"
    )


def _risk_summary(profile, latest):
    if not profile and not latest:
        return (
            "I need your health data to assess risk.\n\n"
            "👉 Please complete your **Profile** and log your vitals in **Log Vitals** first."
        )
    score = 0
    flags = []
    conds = []
    if profile and profile.chronic_conditions:
        try:
            conds = json.loads(profile.chronic_conditions)
        except Exception:
            pass
    if profile and profile.age and profile.age > 60:
        score += 1
        flags.append("Age above 60")
    if conds:
        score += len(conds)
        flags.extend([c.replace('_', ' ').title() for c in conds])
    if profile and profile.bmi and profile.bmi >= 30:
        score += 1
        flags.append(f"Obese (BMI {profile.bmi})")
    elif profile and profile.bmi and profile.bmi >= 25:
        flags.append(f"Overweight (BMI {profile.bmi})")
    if profile and profile.smoking_status == 'current':
        score += 2
        flags.append("Active smoker")
    if latest:
        if latest.blood_pressure_systolic and latest.blood_pressure_systolic >= 140:
            score += 2
            flags.append(f"High BP ({latest.blood_pressure_systolic}/{latest.blood_pressure_diastolic} mmHg)")
        if latest.blood_sugar and latest.blood_sugar >= 126:
            score += 2
            flags.append(f"High blood sugar ({latest.blood_sugar} mg/dL)")

    if score == 0:
        level, color = "🟢 Low", "No major risk factors detected."
    elif score <= 2:
        level, color = "🟡 Moderate", "Some risk factors present. Regular monitoring recommended."
    elif score <= 4:
        level, color = "🟠 High", "Multiple risk factors. Please consult your doctor regularly."
    else:
        level, color = "🔴 Critical", "Significant risk factors. Immediate medical consultation strongly advised."

    flag_text = '\n'.join(f"  • {f}" for f in flags) if flags else "  • None identified"
    return (
        f"**Your Risk Assessment:**\n\n"
        f"**Overall Risk: {level}**\n{color}\n\n"
        f"**Risk factors identified:**\n{flag_text}\n\n"
        "👉 Go to **Risk Assessment** page for a full visual breakdown.\n"
        "⚠️ This is informational only — consult your doctor for a clinical evaluation."
    )


def _fallback(msg):
    return (
        "I'm not sure I understood that fully. Here's what I can help you with:\n\n"
        "• Type **'my vitals'** — see your latest health readings\n"
        "• Type **'diet tips'** — get nutrition guidance\n"
        "• Type **'exercise'** — get activity recommendations\n"
        "• Type **'my medications'** — see medication reminders\n"
        "• Type **'blood pressure'** — get BP guidance\n"
        "• Type **'blood sugar'** — get diabetes tips\n"
        "• Type **'my risk'** — see your risk assessment\n"
        "• Type **'emergency'** — get emergency numbers\n\n"
        "You can also ask naturally, like: *'What should I eat?'* or *'I have a headache'*"
    )


# ── Main dispatcher ────────────────────────────────────────────────────────

def get_response(message: str, profile=None, latest_record=None, medications=None):
    """
    Returns (response_text, agent_label) tuple.
    No external API calls — fully rule-based.
    """
    msg = message.strip()
    meds = medications or []

    if _match(msg, _GREETING):
        return _greeting(profile, latest_record), "HealthGuard"

    if _match(msg, _EMERGENCY):
        return _emergency_info(), "Emergency"

    if _match(msg, _VITALS) or msg.lower() in ('my vitals', 'my health', 'how am i doing'):
        return _vitals_summary(profile, latest_record), "Vitals"

    if _match(msg, _RISK):
        return _risk_summary(profile, latest_record), "Risk Assessment"

    if _match(msg, _BP):
        return _bp_advice(profile, latest_record), "Blood Pressure"

    if _match(msg, _SUGAR):
        return _sugar_advice(profile, latest_record), "Blood Sugar"

    if _match(msg, _MEDICATION):
        return _medication_advice(meds), "Medication"

    if _match(msg, _DIET):
        return _diet_advice(profile), "Diet & Nutrition"

    if _match(msg, _EXERCISE):
        return _exercise_advice(profile), "Exercise"

    if _match(msg, _SLEEP):
        return _sleep_advice(), "Sleep"

    if _match(msg, _STRESS):
        return _stress_advice(), "Mental Wellbeing"

    if _match(msg, _WEIGHT):
        return _weight_advice(profile), "Weight Management"

    if _match(msg, _SYMPTOM):
        return _symptom_advice(msg), "Symptom Guidance"

    return _fallback(msg), "HealthGuard"
