# Pharmacy Product Expiry Alert Management System

> **Final Year Project Deliverable**  
> A web-based pharmaceutical inventory and automated expiry-alert management system featuring category-based dynamic lead times, automatic ABC/VED Pareto classification, multi-channel escalating notifications, in-browser barcode scanning, and closed-loop audit action tracking.

---

## 🌟 Key Features & Academic Contributions

1. **Configurable Category-Based Alert Thresholds**: Avoids hardcoded 30-day rules. Admin-configurable lead times per category (e.g. 90 days for *Critical/High-Value*, 60 days for *Standard*, 30 days for *Fast-Moving*).
2. **Automatic ABC/VED Rule-Based Classifier**: Pareto inventory value ranking combined with VED criticality tags to auto-classify ABC tiers and recommend category lead-time windows (`classify_drugs` management command).
3. **Multi-Channel Escalating Notifications**: Celery-scheduled tasks send Email + SMS alerts. Alerts unacknowledged after 48 hours escalate level and assign a supervisor contact.
4. **Colour-Coded Severity Dashboard**: Red (&lt;7 days / expired) and Amber (within lead time) active alerts table with Red/Amber/Green counter cards. Green count is computed dynamically to avoid table bloat.
5. **In-Browser Barcode/QR Scanning**: Live camera scanner (`html5-qrcode`) for quick stock entry and lookup.
6. **Closed-Loop Action Tracking**: Staff record specific actions (*Removed from shelf*, *Discounted*, *Returned to supplier*, *Disposed*, *No action needed*). Server-enforced mandatory reason text for "No action needed" creates a regulatory compliance audit trail.
7. **Role-Based Access Control (RBAC)**: Pure JWT authentication (`djangorestframework-simplejwt`). Dedicated permissions for `Admin`, `Pharmacist`, and `Supervisor`.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14, Django 6.0, Django REST Framework, SimpleJWT
- **Database**: PostgreSQL (Primary production DB with SQLite dev fallback)
- **Background Tasks**: Celery + Redis (Celery Beat daemon for persistent background execution)
- **Frontend**: React, Vite, Tailwind CSS, Lucide Icons, `html5-qrcode`
- **Notifications**: Twilio (SMS), SendGrid / Django Email Backend (Email with dev console fallback)

---

## 🚀 Setup & Execution Guide

### 1. Backend Setup

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows / Linux)
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations accounts inventory alerts
python manage.py migrate

# Seed database with default categories, demo accounts, and initial stock
python manage.py seed_db

# Run unit test suite
python manage.py test

# Start Django backend server
python manage.py runserver
```

### 2. Demo Accounts (Password for all: `Password123!`)

- **Admin**: `admin@pharmacy.com` (Full access, category rules, user management)
- **Pharmacist**: `pharmacist@pharmacy.com` (Dashboard, stock entry, alert actions)
- **Supervisor**: `supervisor@pharmacy.com` (Dashboard, stock entry, escalations, compliance audit log)

---

## ⏰ Running Background Tasks (Celery + Celery Beat)

To satisfy the non-functional requirement that expiry checks run consistently even when no user is logged in, start the Redis service, Celery worker, and persistent Celery Beat daemon:

```bash
# Terminal 1: Start Celery Worker
celery -A pharm_system worker --loglevel=info

# Terminal 2: Start Celery Beat Persistent Daemon
celery -A pharm_system beat --loglevel=info
```

*Note: For testing during a demo, you can also click **"Run Expiry Scan"** directly on the Dashboard or trigger endpoints `/api/alerts/alerts/trigger_check/` and `/api/inventory/drugs/reclassify/`.*

---

## 💻 Frontend Setup

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start Vite React development server
npm run dev
# App will run at http://localhost:5173
```

---

## 🧪 Test Coverage & Commands

Run the Django automated test suite:

```bash
python manage.py test
```

Tested scenarios:
1. `test_total_value_calculation`: Verifies Python `save()` total value calculation.
2. `test_abc_ved_classification`: Tests ABC Pareto percentage tiering and category suggestions.
3. `test_alert_generation`: Tests Red/Amber alert persistence without Green alert database bloat.
4. `test_escalation_logic`: Tests 48-hour unacknowledged alert escalation and supervisor assignment.
5. `test_action_tracking_validation`: Verifies server-side API rejection of "no_action_needed" without reason text.
6. `test_notification_fallback_when_keys_missing`: Verifies missing Twilio/SendGrid keys log to console without crashing.
7. `test_permission_classes`: Verifies RBAC restrictions per endpoint.

---

## 🎓 Viva Defense Talking Points

1. **Why ABC/VED logic instead of heavy ML (ARIMA/LSTM)?**
   - Community pharmacies frequently lack multi-year cleaned historical sales data required for complex ML models. Rule-based ABC/VED provides explainable, deterministic lead times without data science overhead.
2. **Why category-based lead times over a single 30-day threshold?**
   - High-value/vital drugs (e.g. Biologics) require longer lead times (e.g. 90 days) for supplier returns or specialized discount strategies, whereas fast-moving generics only require 30 days.
3. **Why multi-channel escalation?**
   - Research shows passive, single-channel alerts have low action rates (~23%). Automatic escalation to supervisors after 48 hours closes the accountability loop.
# pharmakon
