# Implementation Plan - Pharmacy Product Expiry Alert Management System

A web-based pharmaceutical inventory and automated expiry-alert management system with category-based alert lead times, automatic ABC/VED classification, multi-channel escalating notifications, barcode scanning, and closed-loop action tracking.

---

## Architecture Overview

```
                           +-------------------------------------+
                           |    React + Tailwind CSS Frontend    |
                           |  (Dashboard, Barcode, Actions, Admin|
                           +------------------+------------------+
                                              |
                                    REST API  | JWT Auth (SimpleJWT)
                                              v
                           +-------------------------------------+
                           |    Django REST Framework Backend    |
                           |  (apps: accounts, inventory, alerts)|
                           +--------+-------------------+--------+
                                    |                   |
                                    v                   v
                        +-------------------+   +--------------------+
                        | PostgreSQL (Primary|   |   Celery + Redis   |
                        |   or SQLite test) |   | (Expiry & Escalation|
                        +-------------------+   |   Scheduled Jobs)  |
                                                +---------+----------+
                                                          |
                                           Twilio / SendGrid (or Console Log fallback)
```

---

## Technical Refinements & User Feedback Incorporated

> [!IMPORTANT]
> **Key Architecture Decisions**:
> 1. **Primary Database**: PostgreSQL is pinned as primary for full audit-log performance and defense compliance.
> 2. **Cross-Backend Compatibility & Schema Alignment**:
>    - `channels_used`: Modeled as `models.JSONField` (works identically on PostgreSQL and SQLite). *Note: Documentation/ERD will reflect JSONField to match build.*
>    - `total_value`: Computed in Django `save()` method (`self.total_value = self.unit_cost * self.quantity`) and exposed as a model field/property.
> 3. **Alert Persistence Strategy**:
>    - Only **Red** (<7 days / expired) and **Amber** (<= category alert lead time) alerts are persisted as active alert rows.
>    - **Green** (safe stock) is computed dynamically: `active_drugs_count - open_alerts_count`, preventing table bloat.
> 4. **Authentication**: Pure **JWT Authentication** (`djangorestframework-simplejwt`). No user role selection at login; role is derived strictly from `request.user.role`.
> 5. **Closed-Loop Audit Enforcement**: Mandatory `reason` validation for `"no_action_needed"` enforced **server-side** in DRF serializers as well as UI.
> 6. **Background Automation**: Celery Beat documented as a background daemon process for hands-free daily execution.

---

## Proposed Changes

### Component 1: Django Backend (`accounts`, `inventory`, `alerts`)

#### [NEW] [settings.py](file:///c:/Users/Fulfilled/dev/Pharm-System/backend/pharm_system/settings.py)
- Django configuration, DRF settings, SimpleJWT (`REST_FRAMEWORK` default auth), CORS headers, Celery & Celery Beat schedule configuration.

#### [NEW] [accounts app](file:///c:/Users/Fulfilled/dev/Pharm-System/backend/accounts)
- Custom `User` model: `id`, `full_name`, `email` (unique), `phone`, `role` (`admin`, `pharmacist`, `supervisor`), `is_active`, `created_at`.
- Endpoints:
  - `POST /api/accounts/login/` (JWT token obtain)
  - `POST /api/accounts/token/refresh/`
  - `GET /api/accounts/me/` (Returns authenticated user profile + role)
  - `GET/POST /api/accounts/users/` (Admin user management)
- DRF Custom Permissions: `IsAdminUserRole`, `IsPharmacistUserRole`, `IsSupervisorUserRole`.

#### [NEW] [inventory app](file:///c:/Users/Fulfilled/dev/Pharm-System/backend/inventory)
- Models:
  - `DrugCategory`: `id`, `name`, `alert_lead_time_days`, `description`, `updated_by` (FK User), `updated_at`.
  - `Drug`: `id`, `name`, `generic_name`, `batch_number`, `manufacture_date`, `expiry_date`, `quantity`, `unit_cost`, `total_value`, `criticality` (`vital`/`essential`/`desirable`), `abc_tier` (`A`/`B`/`C`), `category` (FK DrugCategory), `barcode` (unique), `created_by` (FK User), `created_at`, `updated_at`.
  - DB Indexes: `expiry_date`, `category_id`, `barcode`.
- Services (`services.py`):
  - Pareto cumulative analysis calculation over inventory `total_value` setting `abc_tier` (A: ~70%, B: ~20%, C: ~10%).
  - Rule-based category mapping: Vital or A-tier -> `Critical/High-Value`; Essential or B-tier -> `Standard`; Desirable/C-tier -> `Fast-Moving`.
- Management Command `classify_drugs`: Triggered via CLI or automatically after drug creation/update.

#### [NEW] [alerts app](file:///c:/Users/Fulfilled/dev/Pharm-System/backend/alerts)
- Models:
  - `Alert`: `id`, `drug` (FK Drug), `severity` (`red`/`amber`), `triggered_at`, `channels_used` (JSONField), `escalation_level` (int), `escalated_to` (FK User), `acknowledged` (bool), `acknowledged_by` (FK User), `acknowledged_at`.
  - `AlertAction`: `id`, `alert` (FK Alert), `action_type` (`removed_from_shelf`/`discounted`/`returned_to_supplier`/`disposed`/`no_action_needed`), `reason` (text), `performed_by` (FK User), `performed_at`.
  - `NotificationLog`: `id`, `alert` (FK Alert), `channel` (`email`/`sms`), `recipient`, `sent_at`, `status` (`sent`/`failed`/`delivered`).
- Serializers & Server Validation:
  - Validates `action_type == 'no_action_needed'` requires non-empty `reason`.
- Celery Tasks (`tasks.py`):
  - `check_expiring_drugs`: Daily task finding drugs where `(expiry_date - today) <= category.alert_lead_time_days`. Creates Red (<7 days / expired) or Amber (<= lead_time) alert if no open alert exists. Dispatches email + SMS.
  - `escalate_unacknowledged_alerts`: Task identifying alerts unacknowledged 48+ hours after `triggered_at`. Resends notification, bumps `escalation_level`. If level >= 2, assigns `escalated_to` a supervisor and notifies them.
- Notifications (`notifications.py`): Twilio SMS & SendGrid/Email integration with console fallback when API keys are absent.

#### [NEW] [Seed Data Script](file:///c:/Users/Fulfilled/dev/Pharm-System/backend/inventory/management/commands/seed_db.py)
- Seeds initial `DrugCategory` rows:
  - `Critical/High-Value` (90 days)
  - `Standard` (60 days)
  - `Fast-Moving` (30 days)
- Seeds test accounts (Password: `Password123!`):
  - `admin@pharmacy.com` (Admin)
  - `pharmacist@pharmacy.com` (Pharmacist)
  - `supervisor@pharmacy.com` (Supervisor)
- Seeds sample inventory spanning Red, Amber, and Green expiry states.

---

### Component 2: Frontend (React + Vite + Tailwind CSS)

#### [NEW] [frontend app](file:///c:/Users/Fulfilled/dev/Pharm-System/frontend)
- **Tech**: React + Vite + Tailwind CSS + Lucide Icons + `html5-qrcode` + Axios.
- **Authentication**: JWT token stored in memory/localStorage, auto-attaching `Authorization: Bearer <token>` to requests. User role extracted from `/api/accounts/me/`.
- **Views**:
  - `Login`: Standard credentials form (email + password).
  - `Dashboard`: Red / Amber / Green severity cards + urgent expiring stock table. Green count computed dynamically (`Total Drugs - Active Alerts`).
  - `Stock Intake & Barcode Scanner`: Real-time camera barcode scanner (`html5-qrcode`) with drug lookup and manual form fallback. ABC/VED category auto-suggestion upon entry.
  - `Alert Action Modal`: Closed-loop action dialog with required reason enforcement for "No action needed".
  - `Admin Category & Threshold Config`: Admin-only view to configure lead-time days and manage user accounts.
  - `Audit Log`: Comprehensive action trail for compliance reporting.

---

### Component 3: Configuration & Documentation

#### [NEW] [.env.example](file:///c:/Users/Fulfilled/dev/Pharm-System/.env.example)
- PostgreSQL config (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), Redis URL, Twilio credentials, SendGrid/Email config.

#### [NEW] [README.md](file:///c:/Users/Fulfilled/dev/Pharm-System/README.md)
- Complete step-by-step setup instructions, including PostgreSQL creation, Celery worker & Celery Beat daemon commands, migration commands, ERD diagram details, and demo credentials.

---

## Verification Plan

### Automated Tests
- Django Test Suite (`python manage.py test`):
  - `test_total_value_calculation`: Verify `save()` computes `total_value` accurately.
  - `test_abc_ved_classification`: Test ABC percentage tiering and category suggestions.
  - `test_alert_generation`: Test Red/Amber persistence without Green alert bloat.
  - `test_escalation_logic`: Test 48-hour escalation to supervisor after 2 iterations.
  - `test_action_tracking_validation`: Verify API rejects `"no_action_needed"` without a reason text.
  - `test_notification_fallback_when_keys_missing`: Verify missing Twilio/SendGrid API keys log to console & NotificationLog without raising unhandled exceptions.
  - `test_permission_classes`: Verify role-based access control endpoints.

### Manual Verification Walkthrough
1. Run database migrations & `seed_db`.
2. Login as `pharmacist@pharmacy.com`, scan/add stock, verify dynamic ABC/VED category recommendation.
3. Trigger `check_expiring_drugs` and verify Red/Amber alerts appear on dashboard with correct dynamic Green count.
4. Perform a closed-loop action (e.g. "Disposed" or "No action needed" with reason) and verify alert resolution and audit log update.
5. Login as `admin@pharmacy.com` and change `Critical/High-Value` lead time from 90 to 120 days; re-run check and verify updated alert thresholds.
