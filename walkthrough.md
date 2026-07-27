# Project Completion Walkthrough - Pharmacy Product Expiry Alert Management System

The **Pharmacy Product Expiry Alert Management System** final year project has been fully built, seeded, tested, and verified end-to-end.

---

## 🎯 Completed Deliverables & Accomplishments

### 1. Django REST Framework Backend (`backend/`)
- **Apps & Architecture**: Decoupled into `accounts`, `inventory`, and `alerts` apps.
- **Data Models**:
  - `User`: Custom user model with `role` (`admin`, `pharmacist`, `supervisor`), `email`, `full_name`, `phone`.
  - `DrugCategory`: Dynamic category lead times (`alert_lead_time_days`, `name`, `description`). Default seed rows: *Critical/High-Value* (90 days), *Standard* (60 days), *Fast-Moving* (30 days).
  - `Drug`: `name`, `generic_name`, `batch_number`, `manufacture_date`, `expiry_date`, `quantity`, `unit_cost`, `total_value` (computed via Python `save()`), `criticality` (`vital`/`essential`/`desirable`), `abc_tier` (`A`/`B`/`C`), `category`, `barcode` (unique, indexed).
  - `Alert`: `drug`, `severity` (`red`/`amber`), `triggered_at`, `channels_used` (`JSONField`), `escalation_level`, `escalated_to`, `acknowledged`, `acknowledged_by`, `acknowledged_at`.
  - `AlertAction`: Closed-loop audit log (`action_type`, `reason`, `performed_by`, `performed_at`). Server-side serializer validation enforces mandatory reason text for `"no_action_needed"`.
  - `NotificationLog`: Audit record of dispatched Email/SMS notifications.
- **Algorithms & Classification Service**:
  - `run_abc_ved_classification()`: Pareto cumulative value analysis combined with VED criticality tags to assign ABC tiers and suggest category lead times.
  - `classify_drugs` management command.
  - `seed_db` management command: Seeds categories, demo accounts (`admin@pharmacy.com`, `pharmacist@pharmacy.com`, `supervisor@pharmacy.com` with password `Password123!`), and sample inventory.
- **Background Tasks & Notifications**:
  - `check_expiring_drugs`: Daily task creating Red (<7 days / expired) and Amber (within lead time) alerts. Safe stock is computed dynamically to avoid database bloat.
  - `escalate_unacknowledged_alerts`: Task escalating 48+ hour unacknowledged alerts to supervisors.
  - Safe notification wrapper: Twilio SMS + Email with console logging fallback.
- **Authentication**: JWT authentication (`djangorestframework-simplejwt`). Role-based permission classes (`IsAdminRole`, `IsPharmacistRole`, `IsSupervisorRole`).

---

### 2. React + Tailwind CSS Frontend (`frontend/`)
- **Visual Severity Dashboard**: Red / Amber / Green visual counters + urgent near-expiry alerts table.
- **Camera Barcode/QR Scanner**: In-browser scanner (`html5-qrcode`) with real-time barcode lookup and manual entry fallback.
- **Closed-Loop Action Modal**: Interactive modal for recording staff response (*Removed from shelf*, *Discounted*, *Returned to supplier*, *Disposed*, *No action needed*).
- **Admin Category Rules**: Admin UI for editing dynamic lead-time thresholds and running manual ABC/VED reclassification.
- **Compliance Audit Log**: Complete history of alert actions and notification delivery logs.
- **One-Tap Demo Logins**: Quick sign-in buttons for Pharmacist, Supervisor, and Admin demo testing.

---

## 🧪 Automated Verification & Test Results

The Django test suite was executed and passed with 100% success (7/7 tests passed):

```bash
Creating test database for alias 'default'...
.......
----------------------------------------------------------------------
Ran 7 tests in 17.226s

OK
Destroying test database for alias 'default'...
```

### Verified Test Cases:
1. `test_total_value_calculation`: Verified `save()` calculates `total_value` accurately across backends.
2. `test_abc_ved_classification`: Tested Pareto cumulative percentage tiering and category suggestions.
3. `test_alert_generation`: Tested Red/Amber alert persistence without Green alert table bloat.
4. `test_escalation_logic`: Verified 48-hour unacknowledged alert level increment and supervisor assignment.
5. `test_action_tracking_validation`: Verified DRF API rejects `"no_action_needed"` without a reason text.
6. `test_notification_fallback_when_keys_missing`: Verified missing Twilio/SendGrid API keys log cleanly without raising exceptions.
7. `test_permission_classes`: Verified role-based endpoint permissions.

---

## 📦 Production Frontend Build Verification

The React + Tailwind frontend bundle built cleanly via Vite:

```bash
vite v8.1.5 building client environment for production...
transforming...✓ 1861 modules transformed.
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-Dh9PtR8z.css   44.36 kB │ gzip:   7.30 kB
dist/assets/index-D3acvbAK.js   659.51 kB │ gzip: 198.56 kB
✓ built in 596ms
```

---

## 🚀 Quick Start Instructions for Demo

1. **Backend**:
   ```bash
   cd backend
   .\.venv\Scripts\python.exe manage.py runserver
   ```
2. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser and click any of the **Quick Demo Login** buttons (*Pharmacist*, *Supervisor*, or *Admin*).
