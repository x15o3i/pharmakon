# PHARMACY PRODUCT EXPIRY ALERT MANAGEMENT SYSTEM
## Final Year Project Technical & Architectural Documentation

---

## 1. Executive Summary & Problem Statement

### 1.1 Project Overview
The **Pharmacy Product Expiry Alert Management System** is a full-stack software solution built to mitigate drug inventory waste, enforce financial accountability via **Pareto ABC/VED Analysis**, and ensure audit-compliant closed-loop responses for expiring pharmaceutical stock.

### 1.2 Problem Statement
Pharmaceutical waste due to undetected stock expiration represents a major operational and financial vulnerability in hospital and community pharmacies:
- **Financial Waste**: High-cost medications (e.g., oncology biologics, specialty injections, specialty insulin) expire on pharmacy shelves unnoticed because traditional inventory systems rely on manual stock checks.
- **Clinical & Patient Safety Hazards**: Dispensing expired pharmaceuticals introduces grave clinical risks, including reduced therapeutic efficacy, chemical degradation toxicity, and severe legal liabilities.
- **Absence of Accountability**: Stock removals often lack structured audit trails, masking stock shrinkage and inventory discrepancies.

### 1.3 Solution & Objectives
This project solves these issues by delivering:
1. **Category Lead-Time Rules**: Dynamic risk windows assigned by category (`Critical/High-Value`: 90 days, `Standard`: 60 days, `Fast-Moving`: 30 days) with a enforced mathematical floor of **8 days** to prevent Amber warning skipping.
2. **Pareto ABC/VED Classification Engine**: Automatically ranks stock by financial value (Tier A top 80%, Tier B next 15%, Tier C remaining 5%) integrated with clinical criticality tags (`Vital`, `Essential`, `Desirable`).
3. **Automated Background Scans & 48-Hour Escalation**: Celery background tasks perform daily expiry scans and escalate unacknowledged alerts to supervisors after 48 hours, enforced by a 48-hour notification throttling window.
4. **Closed-Loop Audit Protocol**: Enforces documented resolution actions (`Removed from Shelf`, `Discounted`, `Returned to Supplier`, `Disposed`, `No Action Needed`) with mandatory written explanations for "No Action Needed".
5. **Multi-Channel Alert Dispatch**: Transmits notifications across **Twilio SMS**, **Twilio WhatsApp**, and **Email**, with graceful console fallback logging.
6. **Mobile Barcode & Image Scanner**: Decodes 1D linear barcodes (EAN-13 `6156000468334`, Code-128, Code-39, UPC) and 2D QR codes via live camera streaming or photo upload.

---

## 2. System Architecture & High-Level Design

The system implements a multi-tier, decoupled architecture:

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Layer (React 19 + Bootstrap 5 + Vite)"]
        UI[Dashboard / Stock Intake / Inventory Directory / Audit Log / Admin Rules]
        Scanner[Wasm Live Camera & Photo Barcode Reader]
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

## 3. Technology Stack Specification

| Component | Technology | Version | Key Responsibilities |
|---|---|---|---|
| **Backend Core** | Python / Django | Python 3.12, Django 5.x | REST API server, ORM modeling, business logic rules |
| **API Framework** | Django REST Framework | v3.14+ | Serializers, ViewSets, permission classes |
| **Authentication** | `djangorestframework-simplejwt` | v5.3+ | Stateless JWT access and refresh token management |
| **Database** | Neon PostgreSQL | PostgreSQL 16+ | Cloud serverless relational database |
| **Database Adapters** | `psycopg2-binary`, `dj-database-url` | v2.9+ / v3.0+ | Connection pooling & `DATABASE_URL` parsing |
| **Async Task Queue** | Celery + Redis | Celery 5.x, Redis 5.x | Background scheduled scans and escalation jobs |
| **Static Asset Serving** | Whitenoise | v6.12+ | Production static file collection for serverless hosts |
| **Frontend Core** | React / Vite | React 19, Vite 8.x | Dynamic Single Page Application (SPA) |
| **UI Design System** | Bootstrap 5, Bootstrap Icons | v5.3.8 / v1.13+ | Responsive layout, cards, modals, and tables |
| **Barcode Engine** | `html5-qrcode` | v2.3.8 | Wasm camera barcode decoder & file photo parser |
| **Mobile HTTPS Server** | `@vitejs/plugin-basic-ssl` | v1.x | Local SSL certificate server for mobile camera API access |
| **Notification Services** | Twilio API, Django Mail | Twilio SDK v8.x | SMS, WhatsApp, and Email alert dispatches |
| **Hosting Platform** | Vercel | Monorepo / Serverless | Web application deployment and API routing |

---

## 4. Database Schema & ER Diagram

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
        integer alert_lead_time_days "MinValueValidator(8)"
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

### Table Specifications & Data Constraints

1. **`users`**:
   - `role`: Choices (`admin`, `pharmacist`, `supervisor`). Enforces granular DRF API permissions ($\text{Admin} \supseteq \text{Supervisor} \supseteq \text{Pharmacist}$).
2. **`drug_categories`**:
   - `alert_lead_time_days`: Positive integer defining category-specific warning windows. Enforces `MinValueValidator(8)` (minimum 8 days) so that the Amber warning window ($7 < \text{days} \le \text{alert\_lead\_time\_days}$) is mathematically impossible to skip.
3. **`drugs`**:
   - `total_value`: Computed in Python `save()` (`unit_cost * quantity`).
   - `barcode`: String indexed with unique constraint.
   - `criticality`: Choices (`vital`, `essential`, `desirable`).
   - `abc_tier`: Choices (`A`, `B`, `C`).
4. **`alerts`**:
   - `severity`: Choices (`red`, `amber`).
   - `channels_used`: `JSONField` storing arrays of notification channels dispatched.
   - `last_escalated_at`: Timestamp tracking 48-hour escalation throttling.
5. **`alert_actions`**:
   - `action_type`: Choices (`removed_from_shelf`, `discounted`, `returned_to_supplier`, `disposed`, `no_action_needed`).
   - `reason`: Mandatory text field when `action_type == 'no_action_needed'`.
6. **`notification_log`**:
   - `channel`: Choices (`email`, `sms`, `whatsapp`).

---

## 5. Algorithms & Mathematical Formulations

### 5.1 Pareto ABC Financial Analysis Algorithm
The system calculates total inventory capital valuation for each drug:

$$\text{Total Valuation}_i = \text{Quantity}_i \times \text{Unit Cost}_i$$

1. Sort all active drugs in descending order of $\text{Total Valuation}_i$.
2. Compute cumulative percentage of total inventory capital:

$$\text{Cumulative Capital Share}_k = \frac{\sum_{i=1}^{k} \text{Total Valuation}_i}{\sum_{j=1}^{N} \text{Total Valuation}_j} \times 100\%$$

3. Assign ABC Tiers based on cumulative thresholds:
   - **Tier A (High Financial Value)**: Drugs contributing to the cumulative top **80%** of inventory value.
   - **Tier B (Medium Financial Value)**: Drugs contributing to the next **15%** of inventory value (80% to 95%).
   - **Tier C (Low Financial Value)**: Drugs contributing to the bottom **5%** of inventory value (95% to 100%).

---

### 5.2 Expiry Risk Assessment & Alert Rules
Given $\text{Days Remaining} = \text{Expiry Date} - \text{Current Date}$:
- **Red Alert (Urgent Risk)**: $\text{Days Remaining} \le 7$ (or expired).
- **Amber Alert (Early Lead-Time Risk)**: $7 < \text{Days Remaining} \le \text{Category Alert Lead Time Days}$.
- **Green (Safe Stock)**: Calculated dynamically in memory ($\text{Total Active Drugs} - \text{Open Alerts}$).

*Note: Since $\text{Category Alert Lead Time Days} \ge 8$, the range $7 < \text{Days Remaining} \le \text{Lead Time}$ is guaranteed non-empty.*

---

### 5.3 48-Hour Unacknowledged Alert Escalation Throttling Logic
To avoid notification spam while ensuring unacknowledged Red alerts get supervisor attention:

$$\text{Unacknowledged Query} = \{ a \in \text{Alerts} \mid a.\text{acknowledged} = \text{False} \land (a.\text{last\_escalated\_at} \le t - 48\text{h} \lor (a.\text{last\_escalated\_at is NULL} \land a.\text{triggered\_at} \le t - 48\text{h})) \}$$

Upon match:
1. Assign `escalated_to` to an available **Supervisor** account.
2. Increment `escalation_level` by 1.
3. Update `last_escalated_at = timezone.now()`.
4. Trigger multi-channel dispatches (SMS, WhatsApp, Email).

---

### 5.4 Closed-Loop Validation Algorithm
When staff submit an alert action:
```python
if action_type == AlertAction.ActionType.NO_ACTION_NEEDED and not reason.strip():
    raise serializers.ValidationError({
        "reason": "A mandatory explanation is required when selecting 'No Action Needed'."
    })
```

---

## 6. REST API Reference

| Endpoint | Method | Permission | Description |
|---|---|---|---|
| `/api/accounts/login/` | `POST` | Public | Authenticate staff & return JWT access/refresh tokens |
| `/api/accounts/users/` | `GET` | Admin | List all staff user accounts and roles |
| `/api/inventory/categories/` | `GET` | Pharmacist / Supervisor / Admin | List category alert lead-time rules |
| `/api/inventory/categories/` | `POST`, `PUT`, `DELETE` | Admin Only | Create, update, or delete category lead-time rules |
| `/api/inventory/drugs/` | `GET`, `POST` | Pharmacist / Supervisor / Admin | List all drugs or create new stock intake record |
| `/api/inventory/drugs/<id>/` | `DELETE` | Pharmacist / Supervisor / Admin | Remove drug record from inventory |
| `/api/inventory/drugs/barcode/<code_val>/` | `GET` | Pharmacist / Supervisor / Admin | Lookup drug record instantly by barcode number |
| `/api/inventory/drugs/reclassify/` | `POST` | Supervisor / Admin | Manually execute ABC/VED Pareto reclassification |
| `/api/alerts/alerts/dashboard_summary/` | `GET` | Pharmacist / Supervisor / Admin | Fetch Red, Amber, Green counts and active alert list |
| `/api/alerts/alerts/trigger_check/` | `POST` | Pharmacist / Supervisor / Admin | Manually execute daily expiry scan task |
| `/api/alerts/actions/` | `GET`, `POST` | Pharmacist / Supervisor / Admin | View audit actions or record closed-loop resolution |
| `/api/alerts/logs/` | `GET` | Supervisor / Admin | View notification delivery log history |

---

## 7. Frontend User Interface Modules

The frontend is built using **React 19** and styled with **Bootstrap 5**:

1. **Dashboard View (`Dashboard.jsx`)**:
   - **Severity Counter Cards**: Interactive Red, Amber, and Green summary cards with hover animations.
   - **Urgency Filter Buttons**: Filter alerts by `All`, `Red Only`, or `Amber Only`.
   - **Action Trigger Modal**: Resolves alerts in real-time.
2. **Stock Intake & Scanner (`StockEntry.jsx`)**:
   - Dual-tab interface: **Stock Inventory List** vs **New Stock Intake**.
   - Live camera scanner & **Upload Barcode Photo** button.
   - Product details form (Trade Name, Generic Name, Batch #, Barcode, Manufacture/Expiry dates, Quantity, Unit Cost, Criticality tag, Category).
3. **Pharmacy Inventory Directory (`InventoryList.jsx`)**:
   - Live search bar (Trade Name, Generic Name, Batch #, Barcode).
   - Category, ABC Tier (Tier A/B/C), and Criticality filters.
   - Financial valuation metrics cards ($ Total Inventory Capital).
   - Full inventory stock table with delete triggers.
4. **Compliance Audit Log (`AuditLog.jsx`)**:
   - Sub-tab views for **Closed-Loop Actions** and **Notification Logs**.
5. **Admin Category & Threshold Rules (`AdminCategories.jsx`)**:
   - Category lead-time threshold editor (minimum 8 days).
   - **Run ABC/VED Classification** engine button.
   - Staff account directory and role permissions matrix.

---

## 8. Multi-Channel Notification Gateway

- **Twilio SMS**: Sends SMS alerts directly to registered staff phone numbers.
- **Twilio WhatsApp**: Transmits formatted messages via Twilio WhatsApp Sandbox (`whatsapp:+14155238886`).
- **Django Email**: Dispatches HTML/Plain text emails.
- **Console Log Fallback**: Gracefully logs messages to standard output if Twilio API keys are absent.

---

## 9. Cloud Deployment & Configuration

### 9.1 Neon Serverless PostgreSQL Database
- **Connection String Format**:
  `DATABASE_URL=postgresql://neondb_owner:password@ep-xxx.neon.tech/neondb?sslmode=require`
- **Dynamic Configuration**: `dj-database-url` parses `DATABASE_URL` with SSL enforcement.

### 9.2 Vercel Deployment Setup
- **Backend (`pharm-backend`)**:
  - Root Directory: `backend`
  - Builder: `@vercel/python` (Python 3.12 serverless runtime via `wsgi.py`)
  - Middleware: `WhiteNoiseMiddleware` for static asset serving.
- **Frontend (`pharm-frontend`)**:
  - Root Directory: `frontend`
  - Builder: `@vercel/static-build` (Vite SPA)
  - API Configuration: Reads `VITE_API_URL` environment variable (`https://pharm-backend-flame.vercel.app/api`).

---

## 10. Automated Testing & Verification Suite

Executed via:
```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test
```

### Verified Test Cases (100% Pass):
- ✅ `test_abc_ved_reclassification`: Validates Pareto cumulative financial ranking (Tier A/B/C) and VED matrix integration.
- ✅ `test_alert_trigger_logic`: Verifies Red (<7 days) and Amber alert creation.
- ✅ `test_escalation_logic`: Verifies unacknowledged alert escalation and 48-hour throttling (`last_escalated_at`).
- ✅ `test_closed_loop_action_validation`: Enforces mandatory reason text for `no_action_needed`.
- ✅ `test_notification_fallback_when_keys_missing`: Verifies console-log fallback when Twilio keys are missing.
- ✅ `test_drug_barcode_lookup_endpoint`: Verifies instant barcode search API response.
- ✅ `test_category_lead_time_minimum`: Asserts category lead time $\le 7$ days returns `400 Bad Request` and $\ge 8$ days succeeds (`201 Created`).
- ✅ `test_pharmacist_cannot_modify_categories`: Asserts Pharmacist category modification returns `403 Forbidden` while Admin succeeds (`201 Created`).
- ✅ `test_role_hierarchy_access_to_pharmacist_endpoints`: Asserts Admin and Supervisor roles retain full access to Pharmacist-scoped endpoints ($\text{Admin} \supseteq \text{Supervisor} \supseteq \text{Pharmacist}$).

---

## 11. System Access Credentials

| Role | Email | Password | Granted Access Scope |
|---|---|---|---|
| **Admin** | `admin@pharmacy.com` | `Password123!` | Full System Control (Dashboard, Intake, Audit Log, Category Rules) |
| **Pharmacist** | `pharmacist@pharmacy.com` | `Password123!` | Stock Intake, Barcode Scanner, Expiry Action Resolutions |
| **Supervisor** | `supervisor@pharmacy.com` | `Password123!` | Dashboard, Audit Log, Unacknowledged Alert Escalations |
