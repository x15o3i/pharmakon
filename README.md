# Pharmacy Product Expiry Alert Management System

A full-stack, enterprise-grade software application designed to prevent pharmaceutical inventory waste, enforce financial accountability via Pareto ABC/VED analysis, and maintain audit-compliant closed-loop responses for expiring medical stock.

---

## 📋 Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Design & ER Diagram](#4-database-design--er-diagram)
5. [Algorithms & Key Logic Engines](#5-algorithms--key-logic-engines)
   - [Pareto ABC/VED Classification Engine](#a-pareto-abcved-classification-engine)
   - [Expiry Detection & Escalation Throttling Engine](#b-expiry-detection--escalation-throttling-engine)
   - [Closed-Loop Audit Response Protocol](#c-closed-loop-audit-response-protocol)
   - [Multi-Channel Notification Gateway](#d-multi-channel-notification-gateway)
   - [1D/2D Barcode & Image Recognition Engine](#e-1d2d-barcode--image-recognition-engine)
6. [REST API Reference](#6-rest-api-reference)
7. [Frontend Modules & User Interface](#7-frontend-modules--user-interface)
8. [Installation & Local Setup Guide](#8-installation--local-setup-guide)
9. [Production Cloud Deployment (Vercel & Neon DB)](#9-production-cloud-deployment-vercel--neon-db)
10. [Automated Testing & Verification](#10-automated-testing--verification)

---

## 1. Executive Summary & Problem Statement

### 🎯 Problem Statement
In hospital, clinical, and community pharmacies, drug expiration is a primary cause of financial loss and clinical risk:
- **Financial Waste**: High-value medications (e.g., biologics, oncology drugs, specialty injections) expire on shelves unnoticed due to manual stock monitoring.
- **Clinical & Safety Risks**: Administering expired pharmaceuticals poses severe health hazards to patients and legal liabilities to pharmacy institutions.
- **Lack of Accountability**: Stock removals often occur without documented audit trails, leading to unverified inventory shrinkage.

### 💡 The Solution
The **Pharmacy Product Expiry Alert Management System** addresses these challenges through:
1. **Dynamic Risk Categorization**: Lead-time threshold rules assigned by drug category (`Critical/High-Value`: 90 days, `Standard`: 60 days, `Fast-Moving`: 30 days).
2. **Pareto ABC/VED Inventory Analysis**: Combines cumulative financial valuation (ABC Tier A/B/C) with clinical criticality (Vital, Essential, Desirable) to prioritize high-risk stock.
3. **Automated Background Scans & Escalation**: Celery background jobs detect expiring stock daily and escalate unacknowledged alerts to supervisors after 48 hours while enforcing a 48-hour notification throttling window.
4. **Closed-Loop Audit Trail**: Mandates staff action responses (`Removed from Shelf`, `Discounted`, `Returned to Supplier`, `Disposed`, `No Action Needed`) with mandatory written explanations for "No Action Needed".
5. **Multi-Channel Alert Dispatch**: Delivers notifications via **Twilio SMS**, **Twilio WhatsApp**, and **Email**, with graceful console fallback logging.
6. **Mobile-First Barcode Recognition**: Integrates real-time camera scanning and photo upload decoding for 1D linear barcodes (EAN-13 `6156000468334`, Code-128, Code-39, UPC) and 2D QR codes.

---

## 2. System Architecture

The application adopts a decoupled, multi-tier microservices-compatible architecture:

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Layer (React 19 + Bootstrap 5 + Vite)"]
        UI[Dashboard / Stock Intake / Inventory Directory / Audit Log / Admin Rules]
        Scanner[Wasm Camera & Barcode Photo Reader]
    end

    subgraph APILayer["Backend API Layer (Django REST Framework + SimpleJWT)"]
        Auth[JWT Role-Based Auth: Admin / Pharmacist / Supervisor]
        InvAPI[Inventory API & Barcode Lookup]
        AlertAPI[Alert & Closed-Loop Action API]
    end

    subgraph ServiceLayer["Business Logic & Background Engines"]
        ParetoEngine[ABC/VED Pareto Classifier]
        CeleryWorker[Celery Task Runner + Redis Broker]
        ExpiryScan[check_expiring_drugs]
        EscalationScan[escalate_unacknowledged_alerts]
    end

    subgraph DatabaseLayer["Data Persistence Layer"]
        NeonDB[(Neon Serverless PostgreSQL Database)]
    end

    subgraph NotificationLayer["Multi-Channel Gateway"]
        SMS[Twilio SMS API]
        WhatsApp[Twilio WhatsApp Sandbox]
        Email[Django Email / Console Fallback]
    end

    UI --> Auth
    UI --> InvAPI
    UI --> AlertAPI
    Scanner --> UI

    InvAPI --> NeonDB
    AlertAPI --> NeonDB
    InvAPI --> ParetoEngine
    
    CeleryWorker --> ExpiryScan
    CeleryWorker --> EscalationScan
    ExpiryScan --> NeonDB
    EscalationScan --> NeonDB

    EscalationScan --> SMS
    EscalationScan --> WhatsApp
    EscalationScan --> Email
```

---

## 3. Technology Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Core** | Python / Django | Python 3.12, Django 5.x | REST API server, ORM modeling, business logic rules |
| **API Framework** | Django REST Framework | v3.14+ | Serializers, ViewSets, permission classes |
| **Authentication** | `djangorestframework-simplejwt` | v5.3+ | Stateless JWT access and refresh token management |
| **Database** | Neon PostgreSQL | PostgreSQL 16+ | Cloud serverless relational database |
| **Database Adapter** | `psycopg2-binary`, `dj-database-url` | v2.9+ / v3.0+ | Connection pooling & `DATABASE_URL` parsing |
| **Async Task Queue** | Celery + Redis | Celery 5.x, Redis 5.x | Background scheduled scans and escalation jobs |
| **Static Asset Serving** | Whitenoise | v6.12+ | Production static file collection for serverless hosts |
| **Frontend Core** | React / Vite | React 19, Vite 8.x | Dynamic Single Page Application (SPA) |
| **UI Design System** | Bootstrap 5, Bootstrap Icons | v5.3.8 / v1.13+ | Responsive layout, cards, modals, and tables |
| **Barcode Engine** | `html5-qrcode` | v2.3.8 | Wasm camera barcode decoder & file photo parser |
| **Mobile HTTPS Server** | `@vitejs/plugin-basic-ssl` | v1.x | Local SSL certificate server for mobile camera API access |
| **Notification Services** | Twilio API, Django Mail | Twilio SDK v8.x | SMS, WhatsApp, and Email alert dispatches |
| **Hosting Platform** | Vercel | Monorepo / Serverless | Web application deployment and API routing |

---

## 4. Database Design & ER Diagram

The database schema maps directly to pharmaceutical workflow requirements:

```mermaid
erDiagram
    users ||--o{ drug_categories : "updated_by"
    users ||--o{ drugs : "created_by"
    users ||--o{ alerts : "escalated_to / acknowledged_by"
    users ||--o{ alert_actions : "performed_by"
    drug_categories ||--o{ drugs : "categorizes"
    drugs ||--o{ alerts : "triggers"
    alerts ||--o{ alert_actions : "resolves"
    alerts ||--o{ notification_log : "records"

    users {
        bigint id PK
        string full_name
        string email UK
        string phone
        string password_hash
        string role "admin | pharmacist | supervisor"
        boolean is_active
        datetime created_at
    }

    drug_categories {
        bigint id PK
        string name UK
        integer alert_lead_time_days
        text description
        bigint updated_by FK
        datetime updated_at
    }

    drugs {
        bigint id PK
        string name
        string generic_name
        string batch_number
        date manufacture_date
        date expiry_date
        integer quantity
        decimal unit_cost
        decimal total_value "Calculated in save()"
        string criticality "vital | essential | desirable"
        string abc_tier "A | B | C"
        bigint category_id FK
        string barcode UK
        bigint created_by FK
        datetime created_at
        datetime updated_at
    }

    alerts {
        bigint id PK
        bigint drug_id FK
        string severity "red | amber"
        datetime triggered_at
        datetime last_escalated_at "Nullable - 48h throttling"
        jsonb channels_used
        integer escalation_level
        bigint escalated_to FK
        boolean acknowledged
        bigint acknowledged_by FK
        datetime acknowledged_at
    }

    alert_actions {
        bigint id PK
        bigint alert_id FK
        string action_type "removed_from_shelf | discounted | returned_to_supplier | disposed | no_action_needed"
        text reason "Mandatory for no_action_needed"
        bigint performed_by FK
        datetime performed_at
    }

    notification_log {
        bigint id PK
        bigint alert_id FK
        string channel "email | sms | whatsapp"
        string recipient
        datetime sent_at
        string status "sent | failed | delivered"
    }
```

### 🔑 Key Database Architecture Decisions
1. **Cross-Database Compatibility (`channels_used`)**: Implemented as `models.JSONField` instead of PostgreSQL-only `ArrayField`, ensuring 100% feature parity between PostgreSQL production and SQLite testing backends.
2. **Calculated `total_value` Field**: Computed inside Python `save()` (`self.unit_cost * self.quantity`) to guarantee accurate inventory valuation without relying on database vendor-specific generated columns.
3. **No "Green Alert" Database Bloat**: Safe stock items (Green) are calculated dynamically in memory (`total_active_drugs - open_alerts`). Only **Red** (<7 days) and **Amber** (within category lead time) rows are persisted to the database.

---

## 5. Algorithms & Key Logic Engines

### A. Pareto ABC/VED Classification Engine (`backend/inventory/services.py`)
Combines economic cumulative financial valuation with clinical medical criticality:

$$\text{Total Valuation} = \text{Quantity} \times \text{Unit Cost}$$

1. **ABC Financial Analysis**:
   - Sorts all active drugs in descending order of `total_value`.
   - Computes cumulative percentage of total inventory value:
     - **Tier A (High Financial Value)**: Represents the top **80%** of total inventory capital.
     - **Tier B (Medium Financial Value)**: Represents the next **15%** of total inventory capital.
     - **Tier C (Low Financial Value)**: Represents the remaining **5%** of inventory capital.
2. **VED Matrix Integration**:
   - **Vital (V)**: Life-saving medications with zero stockout tolerance (e.g., Insulin, Epinephrine).
   - **Essential (E)**: Standard prescription drugs (e.g., Antibiotics, Antihypertensives).
   - **Desirable (D)**: Over-the-counter or non-critical supplements (e.g., Vitamins).

---

### B. Expiry Detection & Escalation Throttling Engine (`backend/alerts/tasks.py`)
Triggered daily via Celery Beat or manual scan:

1. **Expiry Threshold Assessment**:
   - **Red Alert**: $\text{Expiry Date} - \text{Today} \le 7\text{ days}$ (or already expired).
   - **Amber Alert**: $7\text{ days} < \text{Expiry Date} - \text{Today} \le \text{Category Lead Time Days}$.
2. **48-Hour Escalation Throttling Query**:
   Finds unacknowledged alerts using the queryset:
   $$\text{Unacknowledged Alerts} = \{ a \in \text{Alerts} \mid a.\text{acknowledged} = \text{False} \land (a.\text{last\_escalated\_at} \le t - 48\text{h} \lor (a.\text{last\_escalated\_at is NULL} \land a.\text{triggered\_at} \le t - 48\text{h})) \}$$
   - Increments `escalation_level` by 1.
   - Assigns alert to a **Supervisor** account.
   - Updates `last_escalated_at = timezone.now()`.
   - Dispatches SMS, WhatsApp, and Email notifications.

---

### C. Closed-Loop Audit Response Protocol (`backend/alerts/views.py` & `ActionModal.jsx`)
Ensures every alert resolution is recorded in an immutable audit trail:
- **Allowed Actions**: `removed_from_shelf`, `discounted`, `returned_to_supplier`, `disposed`, `no_action_needed`.
- **Mandatory Reason Enforcement**: When `action_type === 'no_action_needed'`, DRF server-side validation rejects submissions with empty reasons with a `400 Bad Request` error:
  ```python
  if action_type == AlertAction.ActionType.NO_ACTION_NEEDED and not reason.strip():
      raise serializers.ValidationError({"reason": "A mandatory explanation is required when selecting 'No Action Needed'."})
  ```

---

### D. Multi-Channel Notification Gateway (`backend/alerts/notifications.py`)
Transmits notifications across 3 channels:
- **Twilio SMS**: Sends SMS alerts to registered staff phone numbers.
- **Twilio WhatsApp**: Transmits formatted messages via Twilio WhatsApp Sandbox (`whatsapp:+14155238886`).
- **Django Email**: Dispatches HTML/Plain text emails.
- **Console Log Fallback**: If Twilio credentials (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`) or `TWILIO_WHATSAPP_FROM` are missing, notifications log to standard output without throwing exceptions.

---

### E. 1D/2D Barcode & Image Recognition Engine (`CameraScanner.jsx` & `StockEntry.jsx`)
Powered by `html5-qrcode` WebAssembly decoders:
- **Supported Formats**: `EAN-13` (e.g. `6156000468334`), `EAN-8`, `CODE-128`, `CODE-39`, `UPC-A`, `UPC-E`, `QR_CODE`, `DATA_MATRIX`.
- **Direct Environment Camera Binding**: Invokes `{ facingMode: 'environment' }` directly to prompt native mobile browser permissions for rear cameras.
- **Barcode Photo Upload**: Allows users to select or take a photo of a barcode from their device gallery; `Html5Qrcode.scanFile(file, true)` decodes the barcode automatically.

---

## 6. REST API Reference

| Endpoint | Method | Permission | Description |
|---|---|---|---|
| `/api/accounts/login/` | `POST` | Public | Authenticate staff & return JWT access/refresh tokens |
| `/api/accounts/users/` | `GET` | Admin | List all staff user accounts and roles |
| `/api/inventory/categories/` | `GET`, `POST` | Pharmacist / Admin | List categories or create category lead-time rules |
| `/api/inventory/categories/<id>/` | `PUT` | Admin | Update alert lead time (days) for a category |
| `/api/inventory/drugs/` | `GET`, `POST` | Pharmacist | List all drugs or create new stock intake record |
| `/api/inventory/drugs/<id>/` | `DELETE` | Pharmacist | Remove drug record from inventory |
| `/api/inventory/drugs/barcode/<code_val>/` | `GET` | Pharmacist | Lookup drug record instantly by barcode number |
| `/api/inventory/drugs/reclassify/` | `POST` | Supervisor | Manually execute ABC/VED Pareto reclassification |
| `/api/alerts/alerts/dashboard_summary/` | `GET` | Pharmacist | Fetch Red, Amber, Green counts and active alert list |
| `/api/alerts/alerts/trigger_check/` | `POST` | Pharmacist | Manually execute daily expiry scan task |
| `/api/alerts/actions/` | `GET`, `POST` | Pharmacist | View audit actions or record closed-loop resolution |
| `/api/alerts/logs/` | `GET` | Supervisor | View notification delivery log history |

---

## 7. Frontend Modules & User Interface

The frontend is built using **React 19** and styled with **Bootstrap 5**:

1. **Dashboard View (`Dashboard.jsx`)**:
   - **Severity Counter Cards**: Interactive Red, Amber, and Green summary cards with hover animations.
   - **Urgency Filter Buttons**: Filter alerts by `All`, `Red Only`, or `Amber Only`.
   - **Action Trigger Modal**: Resolves alerts in real-time.
2. **Stock Intake & Scanner (`StockEntry.jsx`)**:
   - Dual-tab interface: **Stock Inventory List** vs **New Stock Intake**.
   - Live camera scanner & **Upload Barcode Photo** button.
   - Full input form for trade name, generic name, batch #, barcode, manufacture/expiry dates, quantity, unit cost, criticality tag, and category.
3. **Pharmacy Inventory Directory (`InventoryList.jsx`)**:
   - Live search bar (Trade Name, Generic Name, Batch #, Barcode).
   - Category, ABC Tier (Tier A/B/C), and Criticality filters.
   - Financial valuation metrics cards ($ Total Inventory Capital).
   - Full inventory stock table with delete triggers.
4. **Compliance Audit Log (`AuditLog.jsx`)**:
   - Sub-tab views for **Closed-Loop Actions** and **Notification Logs**.
5. **Admin Category & Threshold Rules (`AdminCategories.jsx`)**:
   - Category lead-time editor (e.g., 90 days, 60 days, 30 days).
   - **Run ABC/VED Classification** engine button.
   - Staff account and system role directory.

---

## 8. Installation & Local Setup Guide

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- Redis Server (for Celery background tasks)

### Step 1: Clone Repository
```powershell
git clone https://github.com/x15o3i/pharmakon.git
cd pharmakon
```

### Step 2: Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_db
python manage.py runserver
```
*(Backend runs at `http://127.0.0.1:8000`)*

### Step 3: Frontend Setup
Open a new terminal:
```powershell
cd frontend
npm install
npm run dev --host
```
*(Frontend runs at `https://localhost:5173` or local Wi-Fi IP)*

---

## 9. Production Cloud Deployment (Vercel & Neon DB)

### A. Database Setup (Neon PostgreSQL)
1. Create a PostgreSQL project on [Neon DB](https://neon.tech).
2. Copy your connection string:
   ```env
   DATABASE_URL=postgresql://neondb_owner:password@ep-xxx.neon.tech/neondb?sslmode=require
   ```

### B. Backend Vercel Deployment (`pharm-backend`)
1. In Vercel, click **Add New -> Project** -> Select `x15o3i/pharmakon`.
2. Set **Root Directory**: `backend`.
3. Set **Framework Preset**: `Other`.
4. Add Environment Variable:
   - `DATABASE_URL` = *(Your Neon DB connection string)*
5. Deploy to obtain backend URL (e.g., `https://pharm-backend-flame.vercel.app`).

### C. Frontend Vercel Deployment (`pharm-frontend`)
1. In Vercel, click **Add New -> Project** -> Select `x15o3i/pharmakon`.
2. Set **Root Directory**: `frontend`.
3. Set **Framework Preset**: `Vite`.
4. Add Environment Variable:
   - `VITE_API_URL` = `https://pharm-backend-flame.vercel.app/api`
5. Deploy!

---

## 10. Automated Testing & Verification

The application includes an automated test suite covering all critical subsystems:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test
```

### Verified Test Cases:
- ✅ `test_abc_ved_reclassification`: Validates Pareto cumulative financial ranking (Tier A/B/C) and VED matrix integration.
- ✅ `test_alert_trigger_logic`: Verifies Red (<7 days) and Amber alert creation.
- ✅ `test_escalation_logic`: Verifies unacknowledged alert escalation and 48-hour throttling (`last_escalated_at`).
- ✅ `test_closed_loop_action_validation`: Enforces mandatory reason text for `no_action_needed`.
- ✅ `test_notification_fallback_when_keys_missing`: Verifies console-log fallback when Twilio keys are missing.
- ✅ `test_drug_barcode_lookup_endpoint`: Verifies instant barcode search API response.
- ✅ `test_user_role_permissions`: Verifies DRF permission classes for Admin, Pharmacist, and Supervisor roles.

---

### 🔑 Demo Accounts (Created by `seed_db`):
- **Admin**: `admin@pharmacy.com` (Password: `Password123!`)
- **Pharmacist**: `pharmacist@pharmacy.com` (Password: `Password123!`)
- **Supervisor**: `supervisor@pharmacy.com` (Password: `Password123!`)
