# LS_KIA — Pre-Testing Checklist & Postman Test Guide
## What Works, What Needs Setup, Step-by-Step

---

## ✅ Honest Status Assessment

| Feature | Status | Notes |
|---|---|---|
| **Live Stream Token (CRUD)** | ✅ Works | Form view, list view fully functional |
| **Status Dashboard** | ✅ Works | Loads, shows 0 counts if no data |
| **Live Stream Dashboard** | ✅ Works | Loads live stream records |
| **REST API (`/auth/`, `/api/`)** | ✅ Works | Generic REST endpoints are active |
| **Generate Live Stream Link API** | ⚠️ Depends | Needs external CCIP camera system connected |
| **Start Camera API** | ⚠️ Depends | Needs FFmpeg server running on the camera server IP |
| **SMS Send API** | ⚠️ Needs Setup | Requires SMS Gateway configured in Odoo UI first |
| **Email Send API** | ✅ Works | Needs Odoo outgoing mail server configured |
| **WhatsApp API** | ❌ Hardcoded Demo | Phone/URL hardcoded — needs update before testing |
| **DMS Integration API** | ✅ Works | Calls `send_live_stream_link()` on token |
| **Reports** | ✅ Works | PDF reports via wkhtmltopdf, Excel via xlsxwriter |

---

## 🛠️ STEP 1: UI Setup (Do This BEFORE Postman)

You must configure a few things in Odoo before any API can work properly.

---

### 1A. Create a Test Company (Dealership)

**Where:** Settings → Companies → New

Fill in:
- **Company Name:** e.g. `Test Kia Dealer`
- **Dealer Code:** e.g. `KIA001`

---

### 1B. Configure Outgoing Email Server

**Where:** Settings → Technical → Email → Outgoing Mail Servers → New

Fill in:
- **Description:** `Gmail SMTP`
- **SMTP Server:** `smtp.gmail.com`
- **SMTP Port:** `587`
- **Connection Security:** `TLS (STARTTLS)`
- **Username:** `your-email@gmail.com`
- **Password:** Your Gmail App Password (not your login password)

> ⚠️ For Gmail, go to Google Account → Security → App Passwords → Generate one for "Mail"

Click **Test Connection** to confirm.

---

### 1C. Configure SMS Gateway

**Where:** Live Streaming → Configuration → SMS Configure → New

> Note: You may need to be in **debug mode** to see this. Add `?debug=1` to the URL.

Fill in:
- **Name:** `My SMS Gateway`
- **Company:** Select your test company
- **Active:** ✅ (checked)
- **SMS API URL:** Your SMS gateway's base URL (e.g. `https://api.example-sms.com/send?apikey=YOUR_KEY`)
- **Is Global:** ✅ (checked, so it applies to all companies)
- **Message Template:** `Dear customer_name, your car regno is being serviced. Watch live: url_decode`
  - The words `customer_name`, `regno`, `url_decode` are auto-replaced by the system.
- **Parameters (val_ids):** Add rows:
  | Name | Value |
  |---|---|
  | `mobile` | `phone` |
  | `message` | `message` |

> If you don't have an SMS gateway, skip this step and SMS tests will return `stage = 'not_found'` (which is expected).

---

### 1D. Create a Test Customer

**Where:** Contacts → New

Fill in:
- **Name:** `Test Customer`
- **Phone:** `+919876543210` (valid Indian mobile format)
- **Email:** `testcustomer@example.com`

---

### 1E. Create a Live Stream Token (Test Record)

**Where:** Live Streaming → Live Streaming → Current LS Data → New

> If you can't see the menu, make sure your user has the `Live Stream Manager` or `Live Stream User` security group.

Fill in:
- **Company:** Your test company
- **Partner (Customer):** Test Customer
- **State:** Set to `Valid`
- **Status:** Set to `Live`
- **Token:** Type any string, e.g. `TESTTOKEN001`
- **URL:** Type a dummy URL, e.g. `https://example.com/watch/TESTTOKEN001`

**Save and note the record ID** (check the URL bar — it shows `/web#id=X`)

---

### 1F. Configure WhatsApp API

**Where:** Live Streaming → Configuration → WhatsApp Configuration → New

Fill in:
- **Name:** `My WhatsApp Gateway`
- **Instance ID:** Your provider's instance ID
- **Token:** Your provider's API token
- **API URL:** Your provider's base URL (e.g. `https://api.whatsapp-provider.com/send`)
- **State:** Select `Live`
- **Company:** Select your test company

---

### 1G. Test Sending SMS from the UI

**Where:** Live Streaming → Live Streaming → Current LS Data

1. Open the test record you created in Step 1E.
2. Click the **Send SMS** button at the top left of the form.
3. The page will reload. 
4. **Verification:** Check the `SMS Status` field on the record. If your SMS Gateway URL was correct, it should show as `Sent` or `Delivered`. If it failed or you used dummy credentials, it might say `Delivery Failed`.

---

### 1H. Test Sending WhatsApp from the UI

**Where:** Live Streaming → Live Streaming → Current LS Data

1. Open the test record from Step 1E again.
2. Click the **Send WhatsApp** button.
3. **Verification:** Navigate to **Live Streaming → Configuration → WhatsApp Log**.
4. You should see a new log entry. Open it to inspect the `Response` tab to see what the API returned (Success or Error code).

---

### 1I. Verify the Dashboard

**Where:** Live Streaming → Dashboard

1. Open the Live Streaming Dashboard.
2. You should see the test record you created reflected in the UI counts (e.g., total live streams).
3. Check **Live Streaming → Live Stream Report** to ensure your test record appears in the reporting lists.

---

## 🧪 STEP 2: Postman Setup

1. Open Postman
2. Go to **Settings → General** → Enable:
   - ✅ Automatically follow redirects
   - ✅ Send cookies with requests (or use Cookie Jar)

---

## 🧪 STEP 3: Authenticate (Login First!)

Every request below needs this session cookie. Run this FIRST.

```
Method: POST
URL: http://localhost:8069/web/session/authenticate
Headers:
  Content-Type: application/json
Body (raw, JSON):
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

**Expected Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "session_id": "...",
        "uid": 2,
        "name": "Administrator",
        ...
    }
}
```

> Postman will save the `session_id` cookie automatically. All subsequent requests will use it.

---

## 🧪 STEP 4: Test the REST API — Get All Live Stream Tokens

```
Method: GET
URL: http://localhost:8069/api/ac.ars.live.stream.token
Headers:
  Content-Type: application/json
```

**Expected:** A list of all token records in JSON format.

If you see data, the REST API is working! ✅

---

## 🧪 STEP 5: Test Send Email API

Replace `1` with the actual ID of your token record from Step 1E.

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

**Expected Response (success):**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "result": true
    }
}
```

**Verify in Odoo UI:** Go to Live Streaming → Current LS Data → Open your token record → Check `Email State` field — it should show `Sent`.

---

## 🧪 STEP 6: Test Send SMS API

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

**Expected Response (SMS gateway configured):**
```json
{ "result": { "result": true } }
```

**Expected Response (SMS gateway NOT configured):**
```json
{ "result": { "result": false } }
```

The `sms_stage` on the token will show:
- `sent` → SMS delivered
- `not_found` → No SMS gateway configured for this company
- `exception` → Invalid phone number format

**Verify in Odoo UI:** Go to Live Streaming → SMS Records (if menu exists) or check `SMS State` on the token.

---

## 🧪 STEP 7: Test Generate Live Stream Link API

> ⚠️ This requires an external CCIP camera system. Without it, it will fail. This is expected.

```
Method: POST
URL: http://localhost:8069/live_stream/generate/link
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

**Without CCIP system:** Will return an error or `false`. This is OK for now — it needs the camera server infrastructure.

---

## 🧪 STEP 8: Test DMS Link Update API

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

## 🧪 STEP 9: Test Status Dashboard Data

This test calls the `get_count` method directly on the model:

```
Method: POST
URL: http://localhost:8069/web/dataset/call_kw/ac.ars.live.streaming/get_count
Headers:
  Content-Type: application/json
Body:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "ac.ars.live.streaming",
        "method": "get_count",
        "args": [],
        "kwargs": {}
    }
}
```

**Expected Response (no data):**
```json
{
    "result": [
        {"id": "1", "name": "Total Dealers", "count": 0},
        {"id": "2", "name": "Live Streaming Dealers", "count": 0},
        {"id": "3", "name": "Non-Live Streaming Dealers", "count": 0}
    ]
}
```

---

## 🧪 STEP 10: Test WhatsApp API

> ✅ **Current State:** The WhatsApp code has been updated! It now dynamically pulls the phone number and URL from the record, as well as the API Key and URL from the `ac.ars.whatsapp.config` settings.

**Before testing WhatsApp, you need to:**
1. Restart the Odoo server.
2. Go to **Live Streaming → Configuration → WhatsApp Configuration** and create a record with your API Key and URL (if needed).
3. The API will now correctly send messages to the dynamic customer phone number.

---

## 📋 Summary Checklist Before Postman

| # | Action | Location | Required For |
|---|---|---|---|
| 1 | Create test company with dealer code | Settings → Companies | Everything |
| 2 | Configure outgoing mail server | Settings → Technical → Email | Email API |
| 3 | Configure SMS gateway record | Live Streaming → Configuration → SMS Configure | SMS API |
| 4 | Create test customer with phone + email | Contacts | SMS + Email API |
| 5 | Create live stream token record | Live Streaming → Current LS Data | All APIs |
| 6 | Note the token record ID | URL bar in Odoo | All API calls |
| 7 | Enable debug mode (`?debug=1`) | Add to URL | Seeing hidden menus |
| 8 | Fix WhatsApp hardcoded values | Code file | WhatsApp API |

---

*Last Updated: September 2026*
