# HealthGuard AI — Chronic Disease Monitoring Platform

**AI-powered chronic disease monitoring using Python Flask + IBM watsonx.ai with IBM Granite Foundation Models.**

---

## Features

| Feature | Description |
|---|---|
| 🔐 Secure Auth | Registration, login, session management with Flask-Login + Bcrypt |
| 👤 Patient Profile | Demographics, chronic conditions, lifestyle, emergency contacts |
| 🩺 Health Monitoring | Daily vitals logging (BP, sugar, HR, SpO2, temperature, weight) |
| 📊 Analytics | Interactive charts with Chart.js for trend analysis |
| 💊 Medications | Medication tracker with active/inactive management |
| 🤖 AI Assistant | IBM Granite-powered chat with 7 specialized AI agents |
| 🛡️ Risk Assessment | AI health risk analysis (Low/Moderate/High/Critical) |
| 📋 Health Reports | AI-generated weekly/monthly/quarterly health summaries |
| 📄 Report Upload | Medical report uploads with AI summarization (PDF → patient-friendly) |
| 🧮 BMI Calculator | Real-time BMI with category and health advice |
| 🚨 Emergency Alerts | Real-time vital sign alerts with emergency numbers |
| 🌙 Dark/Light Mode | Full theme switching persisted in localStorage |

---

## Agentic AI Architecture

The application implements **7 specialized AI agents** powered by IBM Granite:

```
PatientProfileAgent     → Health baseline assessment
SymptomAnalysisAgent    → Symptom analysis with severity detection  
HealthRiskAssessmentAgent → Cardiovascular & diabetes risk scoring
MedicationReminderAgent → Adherence tips & drug timing guidance
LifestyleRecommendationAgent → Indian diet & exercise plans
HealthReportGeneratorAgent → Periodic health summaries
EmergencyAlertAgent     → Critical vital sign detection
```

### Customizing AI Behavior

Edit `AGENT_INSTRUCTIONS` in [`agents.py`](agents.py) to modify:
- Response tone and language
- Safety guidelines
- Indian healthcare context
- Medical disclaimer text
- Emergency protocols

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- IBM Cloud account with watsonx.ai access
- IBM Watson Machine Learning service instance

### 1. Clone & Navigate
```bash
cd chronic_disease_monitor
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create `.env` file from the example:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
SECRET_KEY=your-strong-random-secret-key
DATABASE_URL=sqlite:///chronic_disease.db
IBM_WATSONX_API_KEY=your-ibm-watsonx-api-key
IBM_WATSONX_PROJECT_ID=your-project-id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

### 5. Run the Application
```bash
python app.py
```

Access at: **http://localhost:5000**

---

## IBM watsonx.ai Configuration

### Getting Your Credentials

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Navigate to **watsonx.ai** → Your Project
3. Copy **Project ID** from Project Settings
4. Create an **API Key** from IAM → API Keys
5. Set `IBM_WATSONX_URL` based on your region:
   - US South: `https://us-south.ml.cloud.ibm.com`
   - EU Germany: `https://eu-de.ml.cloud.ibm.com`
   - Tokyo: `https://jp-tok.ml.cloud.ibm.com`

### Available Granite Models
```
ibm/granite-13b-instruct-v2    (recommended)
ibm/granite-8b-code-instruct
ibm/granite-3-8b-instruct
```

---

## Project Structure

```
chronic_disease_monitor/
├── app.py                  # Flask application factory
├── models.py               # SQLAlchemy database models
├── agents.py               # IBM Granite AI agents (AGENT_INSTRUCTIONS here)
├── forms.py                # Flask-WTF form definitions
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example            # Environment template
├── routes/
│   ├── __init__.py
│   ├── auth.py             # Authentication routes
│   ├── dashboard.py        # Dashboard & feature routes
│   └── api.py              # REST API endpoints
├── templates/
│   ├── base.html           # Base layout with sidebar & topbar
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   ├── index.html      # Main dashboard
│   │   ├── profile.html    # Patient profile
│   │   ├── health_monitor.html
│   │   ├── health_history.html
│   │   ├── ai_assistant.html
│   │   ├── medications.html
│   │   ├── reports.html
│   │   ├── medical_reports.html
│   │   ├── risk_assessment.html
│   │   └── bmi_calculator.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
└── static/
    ├── css/main.css        # Custom styles (dark/light theme)
    ├── js/main.js          # Dashboard interactions
    └── uploads/            # Medical report files
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | AI chat (IBM Granite) |
| GET | `/api/health-data` | Get chart data |
| POST | `/api/emergency-check` | Check vitals for emergencies |
| GET | `/api/lifestyle-advice` | AI lifestyle recommendations |
| GET | `/api/stats` | Dashboard statistics |

---

## IBM Cloud Deployment

### Option 1: IBM Cloud Foundry

```bash
# Install IBM Cloud CLI
ibmcloud login
ibmcloud target --cf

# Create manifest.yml
cat > manifest.yml << EOF
applications:
- name: healthguard-ai
  memory: 512M
  instances: 1
  command: gunicorn app:app --workers 2 --bind 0.0.0.0:\$PORT
  buildpack: python_buildpack
  env:
    IBM_WATSONX_API_KEY: your-api-key
    IBM_WATSONX_PROJECT_ID: your-project-id
    SECRET_KEY: your-secret-key
EOF

ibmcloud cf push
```

### Option 2: IBM Code Engine (Container)

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "2"]
```

```bash
ibmcloud ce application create \
  --name healthguard-ai \
  --image your-registry/healthguard-ai \
  --port 8080 \
  --env IBM_WATSONX_API_KEY=your-key \
  --env IBM_WATSONX_PROJECT_ID=your-project-id \
  --env SECRET_KEY=your-secret
```

### Production Database
For production, replace SQLite with PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@host:5432/healthguard
```

Install: `pip install psycopg2-binary`

---

## Security Notes

- **Never commit `.env`** to version control (already in `.gitignore`)
- Rotate `SECRET_KEY` before production deployment
- Use HTTPS in production (SSL/TLS)
- Set `DEBUG=False` in production
- The provided API key in `.env` should be rotated after development

---

## Medical Disclaimer

> This application is an AI-powered health monitoring tool for educational and informational purposes only. It does **not** provide medical diagnosis or replace professional medical advice. Always consult a qualified healthcare professional for medical decisions. In case of emergency, call **112** (India) or visit the nearest emergency room.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python Flask 3.0 |
| AI Engine | IBM watsonx.ai + IBM Granite 13B |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Bootstrap 5.3 + Chart.js 4.4 |
| Auth | Flask-Login + Flask-Bcrypt |
| Forms | Flask-WTF + WTForms |
| PDF | PyPDF2 + ReportLab |
| Deploy | IBM Cloud / Gunicorn |

---

*Built with ❤️ using IBM Granite Foundation Models*
