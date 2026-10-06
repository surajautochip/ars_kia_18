# LS_KIA Modules — API & Workflow Guide
### (Beginner-Friendly: Odoo 11 → Odoo 18 Migration Explained)

---

## Table of Contents

1. [Overview of the System](#1-overview-of-the-system)
2. [Module Map](#2-module-map)
3. [Core Concepts (Odoo 11 vs Odoo 18)](#3-core-concepts-odoo-11-vs-odoo-18)
4. [Module-by-Module Technical & Functional Flow](#4-module-by-module-technical--functional-flow)
   - 4.1 [ac_ars_cc_camera — The Main Live Streaming Engine](#41-ac_ars_cc_camera--the-main-live-streaming-engine)
   - 4.2 [ac_ars_live_stream_dashboard — Live Stream Dashboard](#42-ac_ars_live_stream_dashboard--live-stream-dashboard)
   - 4.3 [ac_ars_status_dashboard — Status Dashboard](#43-ac_ars_status_dashboard--status-dashboard)
   - 4.4 [ac_ars_ip_camera — IP Camera Recording](#44-ac_ars_ip_camera--ip-camera-recording)
   - 4.5 [ac_ars_live_stream_report — Reports Module](#45-ac_ars_live_stream_report--reports-module)
   - 4.6 [ac-hy-dms-login-integration — DMS Connector](#46-ac-hy-dms-login-integration--dms-connector)
   - 4.7 [odoo-rest-api-master — Generic REST API](#47-odoo-rest-api-master--generic-rest-api)
   - 4.8 [ac_ars_sms_api & ac_ars_hy_whatsapp_api](#48-ac_ars_sms_api--ac_ars_hy_whatsapp_api)
5. [Complete Functional Workflow (End-to-End)](#5-complete-functional-workflow-end-to-end)
6. [Migration Changes: What Changed from Odoo 11 to 18](#6-migration-changes-what-changed-from-odoo-11-to-18)
7. [API Reference & Postman Testing Guide](#7-api-reference--postman-testing-guide)
8. [Common Errors & Fixes Applied During Migration](#8-common-errors--fixes-applied-during-migration)

---

## 1. Overview of the System

This system is a **Live Car Servicing Streaming Platform** built for **Kia car dealerships**.

**What it does (in simple words):**
1. When a customer brings their car to a dealership for service, the system generates a secure link.
2. This link is sent to the customer via **SMS** or **Email**.
3. The customer can click the link to watch a **live video feed** of their car being serviced on the workshop bay.
4. The management team can see dashboards showing which dealers have the system installed and whether cameras are online or offline.
5. Reports can be generated showing live streaming activity across dealerships.

---

## 2. Module Map

```
LS_KIA/
│
├── ac_ars_cc_camera/          ← MAIN MODULE: Live Streaming Engine, Token, Camera
├── ac_ars_live_stream_dashboard/   ← Live Stream Dashboard (OWL JS)
├── ac_ars_status_dashboard/   ← Status Dashboard (Dealer-level overview)
├── ac_ars_ip_camera/          ← IP Camera management & recording
├── ac_ars_live_stream_report/ ← PDF/Excel Reports
├── ac_ars_sms_api/            ← SMS sending via 3rd-party API
├── ac_ars_hy_whatsapp_api/    ← WhatsApp sending via HyperTrack API
├── ac-hy-dms-login-integration/ ← DMS (Dealer Management System) Integration
└── odoo-rest-api-master/      ← Generic REST API wrapper for Odoo models
```

**Module Dependencies:**
```
ac_ars_cc_camera  (core)
    ↓
ac_ars_live_stream_dashboard  (needs cc_camera models)
ac_ars_status_dashboard       (needs cc_camera models)
ac_ars_live_stream_report     (needs cc_camera models)
ac_ars_ip_camera              (extends cc_camera)
```

---

## 3. Core Concepts (Odoo 11 vs Odoo 18)

Before we dive in, here are the key differences in how things work:

### 3.1 Model Naming

| Odoo 11 (Old) | Odoo 18 (New, Correct) |
|---|---|
| `live.streaming` | `ac.ars.live.streaming` |
| `live.stream.token` | `ac.ars.live.stream.token` |
| `region.region` | `ac.ars.region.region` |
| `zone.zone` | `ac.ars.zone.zone` |
| `area.area` | `ac.ars.area.area` |

> **Why this matters:** In Odoo 11, many model names did not have a module prefix. During migration to Odoo 18, the models were correctly renamed with the `ac.ars.` prefix to avoid collisions with Odoo standard models. Any file that still used the old names caused a `KeyError` or `TypeError`.

### 3.2 Deprecated Python Decorators

| Odoo 11 (Old) | Odoo 18 (New) |
|---|---|
| `@api.multi` | Removed. Methods work on recordsets by default. |
| `@api.one` | Removed. Use a `for` loop inside the method instead. |
| `@api.model_create_multi` | Now recommended for `create()`. |

### 3.3 Chatter (Messaging Widget)

| Odoo 11 (Old XML) | Odoo 18 (New XML) |
|---|---|
| `<div class="oe_chatter"><field name="message_follower_ids" .../><field name="message_ids" .../></div>` | `<chatter/>` |

> The old Odoo 11 chatter syntax used specific field widgets. In Odoo 18, these have been replaced with a single `<chatter/>` tag that handles everything automatically.

### 3.4 JSON Request Handling in Controllers

| Odoo 11 (Old) | Odoo 18 (New) |
|---|---|
| `request.jsonrequest['params']['key']` | `kw.get('key')` (from `**kw` parameter) |

> In Odoo 11, the controller manually parsed the JSON payload from `request.jsonrequest`. In Odoo 18, when a route is declared as `type='json'`, all JSON body parameters are automatically passed as keyword arguments (`**kw`) to the controller function.

---

## 4. Module-by-Module Technical & Functional Flow

---

### 4.1 `ac_ars_cc_camera` — The Main Live Streaming Engine

**This is the most important module.** All other modules depend on it.

#### Key Files:
| File | Purpose |
|---|---|
| `models/ac_ars_live_streaming.py` | Defines the `ac.ars.live.streaming` model (one record per service visit) |
| `models/ac_ars_live_stream_token.py` | Defines the `ac.ars.live.stream.token` model (manages the secure link) |
| `models/ac_ars_cc_camera_models.py` | Defines Region, Zone, Area, Territory hierarchy models |
| `controllers/controllers.py` | HTTP API endpoints for starting cameras, sending SMS/Email |

#### Key Models:

**`ac.ars.live.streaming`** — The core data record.
```python
# This model stores one record per live stream session.
# Fields:
name            = Char       # The unique token/link string
date            = Datetime   # When the stream was created
cust_name       = Char       # Customer's name
vehicle_no      = Char       # Vehicle registration number
stream_start_time = Datetime # When the stream actually started
stream_end_time   = Datetime # When the stream ended
streaming_duration = Char    # Computed: how long the stream ran (e.g. "45.00 min")
views_duration  = Char       # Computed: total time customer watched
click_count     = Integer    # Computed: how many times customer opened the link
state           = Selection  # 'progress' or 'finished'
company_id      = Many2one   # Which dealership this belongs to
is_viewing      = Boolean    # Did the customer actually watch?
sms_status      = Selection  # 'sent', 'failed', etc.
mail_status     = Selection  # 'sent', 'failed', etc.
```

**`ac.ars.live.stream.token`** — The secure token/link manager.
```python
# This model manages the lifecycle of a live stream invitation.
# ONE token = ONE service appointment for ONE customer
token   = Char          # A unique random string used in the URL
url     = Text          # The full URL sent to the customer
state   = Selection     # 'draft', 'valid', 'invalid'
status  = Selection     # 'live', 'hold', 'completed'
company_id = Many2one   # Which dealership
partner_id = Many2one   # The customer (res.partner)
sale_order_id = Many2one # The service order (sale.order)
camera_rec_ids = Many2many  # All camera recordings for this session
```

#### API Endpoints (in `controllers/controllers.py`):

```
POST  /live_stream/generate/link  → Generates and saves the stream URL
POST  /customer/sms/send          → Sends the URL to the customer via SMS
POST  /customer/email/send        → Sends the URL to the customer via Email
POST  /live_stream/camera/start   → Starts IP camera recording
```

#### How `generate_live_stream_link` works (line by line):

```python
def generate_live_stream_link(self):
    # Step 1: Call push_ccip on the calendar event
    # This contacts the external CCIP camera system and gets back a token + URL
    res = self.event_id.push_ccip(self.resource)
    
    # Step 2: Check if we got a valid response
    if res['token'] and res.get("url"):
        # Step 3: Decode the URL (it may be URL-encoded)
        url_decode = urllib.parse.unquote(res.get("url"))
        # Step 4: Save the token and URL on this record
        self.write({'token': res['token'], 'url': url_decode})
        return True
    else:
        return False
```

---

### 4.2 `ac_ars_live_stream_dashboard` — Live Stream Dashboard

This module provides the real-time **OWL.js** dashboard that technicians and managers see.

#### Key Files:
| File | Purpose |
|---|---|
| `models/ac_ars_dashboard.py` | Python methods that query data for the dashboard |
| `controllers/controllers.py` | `/ls_dashboard/data` HTTP endpoint |
| `static/src/js/dashboard_live_stream.js` | Frontend OWL component logic |
| `static/src/xml/LiveStreamDashboard.xml` | Frontend OWL HTML template |

#### How the Dashboard Works:

```
Browser loads the Dashboard view
    ↓
OWL JavaScript component initializes
    ↓
JS calls multiple ORM methods on 'ac.ars.live.streaming':
    - get_live_stream_records()          → Fetch all current live streams
    - get_live_stream_records_by_optional() → Filter by date/company
    ↓
The server-side Python methods in ac_ars_dashboard.py execute SQL
queries against the database and return JSON data
    ↓
JS renders the data as cards/charts in the browser
```

#### Migration Fix in `controllers/controllers.py`:

**Old Odoo 11 way (WRONG in Odoo 18):**
```python
# This crashes in Odoo 18 because request.jsonrequest doesn't exist
company_id = request.env['res.company'].search([
    ('name', '=', request.jsonrequest['params']['company'])
])
```

**New Odoo 18 way (CORRECT):**
```python
# Parameters are auto-passed as kwargs when type='json'
def DashBoardData(self, **kw):
    company = kw.get('company')      # Read from kwargs
    option = kw.get('option')        # Read from kwargs
    company_id = request.env['res.company'].search([('name', '=', company)])
```

Also fixed: Raw SQL queries used the old table name `live_streaming` — updated to `ac_ars_live_streaming` (the actual PostgreSQL table name for the `ac.ars.live.streaming` model).

---

### 4.3 `ac_ars_status_dashboard` — Status Dashboard

This dashboard shows the **management-level overview** of all dealerships — how many are doing live streaming, how many are not, and grouped by region/zone/area.

#### Key Files:
| File | Purpose |
|---|---|
| `models/models.py` | Python methods: `get_count`, `get_zone_count`, `get_company_count_graph` etc. |
| `models/ls_status_report.py` | `ls.status.report` model — per-dealer status configuration |
| `static/src/js/status_dashboard.js` | Frontend OWL component that calls the API methods |

#### How it Works:

```
Manager opens Status Dashboard
    ↓
OWL JS (status_dashboard.js) calls methods on 'ac.ars.live.streaming' model:
    - get_count()              → Total/Active/Non-Active dealer counts
    - get_zone_count()         → Counts grouped by Zone
    - get_area_count()         → Counts grouped by Area
    - get_state_count()        → Counts grouped by State
    - get_manager_count()      → Counts grouped by Area Manager
    - get_tpsm_count()         → Counts grouped by TPSM
    - get_company_count_graph()→ Data for charts/graphs
    ↓
ApexCharts renders pie/bar charts
```

#### Migration Fixes Applied:

1. **Model name fix** (`models.py` and `ls_status_report.py`):
   ```python
   # OLD (crashes):
   self.env['region.region'].sudo().search([])
   # NEW (works):
   self.env['ac.ars.region.region'].sudo().search([])
   ```

2. **Empty list safety** (`models.py` and `ls_status_report.py`):
   ```python
   # OLD (crashes when no data exists):
   total = int(ls_not_active[0]['count']) + int(ls_active[0]['count'])
   
   # NEW (safe, defaults to 0):
   active_count = int(ls_active[0]['ls_status_count']) if ls_active else 0
   not_active_count = int(ls_not_active[0]['ls_status_count']) if ls_not_active else 0
   total = active_count + not_active_count
   ```

3. **JS model name fix** (`static/src/js/status_dashboard.js`):
   ```javascript
   // OLD (404 error):
   this.orm.call("live.streaming", "get_count", [])
   // NEW (works):
   this.orm.call("ac.ars.live.streaming", "get_count", [])
   ```

---

### 4.4 `ac_ars_ip_camera` — IP Camera Recording

This module manages physical IP cameras installed in the workshop bays.

#### Key Files:
| File | Purpose |
|---|---|
| `models/ac_ars_ip_camera.py` | `ac.ars.ip.camera` model — camera configuration |
| `models/ac_ars_camera_records.py` | `ac.ars.camera.records` — individual recording sessions |

#### How it Works:

```
Service Advisor clicks "Start Stream" on a token
    ↓
ac_ars_live_streaming_camera_start() is called
    ↓
For each camera linked to the service bay resource:
    1. Check if camera is online (test RTSP connection)
    2. Send HTTP GET to the camera recording server:
       http://{server}/start?ip=...&port=...&name=...&RTSP_URL=...
    3. Create an ac.ars.camera.records entry (status='recording')
    4. Save the PID (Process ID) returned by the server
    ↓
When stream ends:
    HTTP GET to http://{server}/stop?pid={pid}
    ac.ars.camera.records status → 'recorded'
```

#### Migration Fix Applied:

```python
# The compute method for 'duration' field MUST always assign a value.
# Old code (crashes on new records with empty dates):
@api.depends('end_date')
def _compute_time(self):
    for case in self:
        if case.start_date and case.end_date:
            case.duration = str(end - start) + " min"
        # ← Missing else! Odoo 18 raises ValueError here.

# Fixed code:
@api.depends('start_date', 'end_date')
def _compute_time(self):
    for case in self:
        if case.start_date and case.end_date:
            case.duration = str(end - start) + " min"
        else:
            case.duration = "0 min"   # ← Always assign a value
```

---

### 4.5 `ac_ars_live_stream_report` — Reports Module

This module generates PDF and Excel reports for live streaming activity.

#### Key Files:
| File | Purpose |
|---|---|
| `wizard/live_streaming_report.py` | Wizard model for Live Utilization Report |
| `wizard/ls_status_report.py` | Wizard model for LS Status Report |
| `report/live_streaming_report.xml` | QWeb PDF template |

#### How Reports Work:

```
User goes to Reports menu → Select a report type
    ↓
A Wizard dialog opens (e.g. choose date range, company)
    ↓
User clicks "Print PDF" or "Download Excel"
    ↓
Wizard's generate method runs:
    - Queries ac.ars.live.streaming records for the given filters
    - For PDF: renders QWeb XML template → wkhtmltopdf converts to PDF
    - For Excel: uses xlsxwriter library to create .xlsx file in memory
    ↓
File is returned as a download to the browser
```

#### Migration Fix (Pandas Removed):

In Odoo 11, the reports used the Python `pandas` library to create Excel files. Pandas is not installed in the Odoo 18 environment, so all Excel generation was rewritten using `xlsxwriter`:

```python
# OLD (Odoo 11, broken):
import pandas as pd
df = pd.DataFrame(data)
df.to_excel(output, index=False)

# NEW (Odoo 18, works):
import xlsxwriter
workbook = xlsxwriter.Workbook(output)
worksheet = workbook.add_worksheet()
for row_idx, row in enumerate(data):
    for col_idx, value in enumerate(row):
        worksheet.write(row_idx, col_idx, value)
workbook.close()
```

---

### 4.6 `ac-hy-dms-login-integration` — DMS Connector

The DMS (Dealer Management System) is an external software used by dealerships to manage service orders. This module provides a bridge between the DMS and Odoo.

#### API Endpoint:
```
POST  /dms/link/update
```

**How it works:**
```
DMS system sends a POST request to Odoo with a token ID
    ↓
Odoo looks up the ac.ars.live.stream.token record by that ID
    ↓
Calls token_obj.send_live_stream_link()
    ↓
The method sends the streaming URL back to the DMS
(so the DMS can display it in the service advisor's screen)
```

---

### 4.7 `odoo-rest-api-master` — Generic REST API

This is a generic REST API wrapper that exposes any Odoo model via HTTP.

#### Available Endpoints:

| Method | URL | Auth | Purpose |
|---|---|---|---|
| `POST` | `/auth/` | None | Login and get session |
| `POST` | `/object/<model>/<function>` | User | Call any model-level method |
| `POST` | `/object/<model>/<id>/<function>` | User | Call any record-level method |
| `GET` | `/api/<model>` | User | Get all records of a model |
| `GET` | `/api/<model>/<id>` | User | Get a specific record |
| `POST` | `/api/<model>` | User | Create a new record |
| `PUT` | `/api/<model>/<id>` | User | Update a record |
| `DELETE` | `/api/<model>/<id>` | User | Delete a record |

---

### 4.8 `ac_ars_sms_api` & `ac_ars_hy_whatsapp_api`

These modules handle outbound notifications to customers.

**SMS Flow:**
```
ac_ars_live_streaming_send_sms() is called on a token
    ↓
Creates an ac.ars.sms.record with customer phone + stream URL
    ↓
Calls sent_an_sms() which makes an HTTP POST to the SMS gateway API
    ↓
Updates the sms_stage field on the token with the result
```

**WhatsApp Flow (similar):**
```
A WhatsApp API call is made via the Hypertrack/HY API
with the customer's phone number and the streaming URL
```

---

## 5. Complete Functional Workflow (End-to-End)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      STEP 1: SERVICE BOOKING                        │
│  Customer calls / walks in → Service Advisor creates a Sale Order   │
│  → A Calendar Event (Appointment) is created in Odoo               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2: TOKEN GENERATION                         │
│  Service Advisor opens the Token form for the appointment           │
│  → Clicks "Generate Live Stream Link"                               │
│  → POST /live_stream/generate/link (with token ID)                  │
│  → Odoo contacts external CCIP system via event.push_ccip()         │
│  → Gets back a unique URL and saves it on the token record          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   STEP 3: NOTIFICATION TO CUSTOMER                  │
│  Advisor clicks "Send SMS" → POST /customer/sms/send                │
│      OR                                                             │
│  Advisor clicks "Send Email" → POST /customer/email/send            │
│  → Customer receives SMS/Email with the unique streaming URL        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 4: STREAM STARTS                            │
│  Advisor clicks "Start Camera" → POST /live_stream/camera/start     │
│  → For each bay camera: HTTP GET to FFmpeg recording server         │
│  → Recording starts, PID (process ID) saved in camera records       │
│  → Token status changes to 'live'                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 5: CUSTOMER WATCHES                           │
│  Customer opens the URL on their phone                              │
│  → Browser loads the live stream                                    │
│  → Each view/click is logged in ac.ars.live.streaming.line          │
│  → click_count and views_duration are computed in real-time         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 6: STREAM ENDS                             │
│  Service completes → Advisor clicks "Finish Stream"                 │
│  → Cameras are stopped via HTTP GET to FFmpeg /stop endpoint        │
│  → ac.ars.live.streaming record gets stream_end_time                │
│  → streaming_duration is computed                                   │
│  → Record is synced to the HQ server via ac_live_stream_server_create│
│  → Token state → 'invalid', status → 'completed'                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              STEP 7: REPORTS & DASHBOARDS                           │
│  Management views Live Stream Dashboard: real-time activity         │
│  Management views Status Dashboard: dealer-level KPIs               │
│  Reports generated: PDF/Excel showing streams by date/dealer/region │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Migration Changes: What Changed from Odoo 11 to 18

| Area | Odoo 11 | Odoo 18 (Fixed) |
|---|---|---|
| Model names | `live.streaming`, `region.region` | `ac.ars.live.streaming`, `ac.ars.region.region` etc. |
| Decorators | `@api.multi`, `@api.one` | Removed — just use `for rec in self:` |
| Chatter XML | `<div class="oe_chatter">...fields...` | `<chatter/>` |
| JSON params in controllers | `request.jsonrequest['params']['key']` | `kw.get('key')` |
| Excel generation | `pandas` library | `xlsxwriter` library |
| Compute methods | Did not need `else` clause | Must always assign to field |
| list widget | `widget="one2many_list"` | `<list>` tag inside field |
| SQL table names | `FROM live_streaming` | `FROM ac_ars_live_streaming` |
| XML ID namespacing | Could reference IDs without module prefix | Must use `module.xml_id` format |

---

## 7. API Reference & Postman Testing Guide

### 7.1 Authentication (Required First!)

All APIs (except public ones) require a session cookie. Use the `/auth/` endpoint first.

**Step 1: Login**
```
Method: POST
URL: http://localhost:8069/auth/
Headers:
    Content-Type: application/json
Body (raw JSON):
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "db": "kia_test",
        "login": "admin",
        "password": "admin"
    }
}
```
> After a successful login, Postman will automatically save the session cookie. **Enable "Automatically follow redirects" and "Save cookies"** in Postman settings.

---

### 7.2 Generate Live Stream Link

**What it does:** Takes a Token record ID and generates the live streaming URL.

```
Method: POST
URL: http://localhost:8069/live_stream/generate/link
Headers:
    Content-Type: application/json
Body (raw JSON):
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "token": 1
    }
}
```

Replace `1` with the actual ID of an `ac.ars.live.stream.token` record.

**Expected Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "result": true
    }
}
```

---

### 7.3 Send SMS to Customer

```
Method: POST
URL: http://localhost:8069/customer/sms/send
Headers:
    Content-Type: application/json
Body:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "token": 1
    }
}
```

---

### 7.4 Send Email to Customer

```
Method: POST
URL: http://localhost:8069/customer/email/send
Headers:
    Content-Type: application/json
Body:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "token": 1
    }
}
```

---

### 7.5 Start Camera Recording

```
Method: POST
URL: http://localhost:8069/live_stream/camera/start
Headers:
    Content-Type: application/json
Body:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "token": 1
    }
}
```

**Expected Response (success):**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "status": true
    }
}
```

**Expected Response (camera not reachable):**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "status": false,
        "message": "Camera could not able to access! Do you want to retry?"
    }
}
```

---

### 7.6 DMS Link Update

```
Method: POST
URL: http://localhost:8069/dms/link/update
Headers:
    Content-Type: application/json
Body:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "token": 1
    }
}
```

---

### 7.7 Generic REST API — Get All Live Streaming Records

```
Method: GET
URL: http://localhost:8069/api/ac.ars.live.streaming
Headers:
    Content-Type: application/json
```
> Requires active user session.

---

### 7.8 Generic REST API — Call a Model Method

This is extremely powerful. You can call ANY method on ANY model:

```
Method: POST
URL: http://localhost:8069/object/ac.ars.live.streaming/get_count
Headers:
    Content-Type: application/json
Body:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {}
}
```

---

### 7.9 Live Dashboard Data

```
Method: POST
URL: http://localhost:8069/ls_dashboard/data
Headers:
    Content-Type: application/json
Body:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "company": "Kia Motors HQ",
        "option": "0"
    }
}
```

---

## 8. Common Errors & Fixes Applied During Migration

| Error | Root Cause | Fix Applied |
|---|---|---|
| `TypeError: Model 'live.streaming' does not exist` | Old model name in Python code | Replaced with `ac.ars.live.streaming` |
| `TypeError: Model 'live.stream.token' does not exist` | Old model name in Python code | Replaced with `ac.ars.live.stream.token` |
| `KeyError: 'region.region'` | Old model name | Replaced with `ac.ars.region.region` |
| `AttributeError: 'Request' has no attribute 'jsonrequest'` | Old JSON parsing | Use `kw.get('key')` instead |
| `IndexError: list index out of range` | No data in DB, `[0]` fails | Added `if ls_active else 0` guard |
| `ValueError: Compute method failed to assign .duration` | Missing `else` in compute | Added `else: case.duration = "0 min"` |
| Form view shows broken fields (Internal fields visible) | Old chatter widget crashed JS | Replaced `oe_chatter div` with `<chatter/>` |
| XML IDs not found (`live_stream_report.some_id`) | Wrong module prefix in XML | Removed incorrect prefix |
| `ModuleNotFoundError: No module named 'pandas'` | Pandas not installed in Odoo 18 | Rewrote with `xlsxwriter` |
| `@api.multi` attribute error | Deprecated in Odoo 18 | Removed decorator |

---

*Generated: September 2026 | Environment: Odoo 18.0-20260326 | Database: kia_test*
