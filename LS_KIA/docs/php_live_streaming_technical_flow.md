# PHP Live Streaming – Technical Documentation

This document provides a technical overview of how the Live Streaming feature is implemented across Odoo 18, the PHP middleware, and the Node.js streaming proxy.

## 1. System Architecture

The Live Streaming architecture consists of four main components:
1.  **Odoo 18 Backend**: Stores camera configurations, manages user sessions, and initiates the stream request.
2.  **PHP Middleware (CodeIgniter)**: Acts as a bridge, generating secure access tokens, managing external access sessions, and serving the frontend video player (`video.js`).
3.  **Node.js Proxy**: A local streaming server that uses `ffmpeg` to consume RTSP streams from the physical IP cameras and transcode them into browser-friendly HLS (`.m3u8`) streams.
4.  **IP Cameras**: The physical hardware serving RTSP streams.

---

## 2. Technical Flow Breakdown

### Step 1: Odoo Initiates the Stream
**Trigger:** A user clicks "Live Streaming" in Odoo.
**Code Path:** `ac_ars_cc_camera/models/ac_ars_live_stream_token.py`
*   Odoo fetches the configured camera(s) for the selected Bay (up to 3 cameras).
*   It encrypts the camera's RTSP username and password.
*   It sends an HTTP `POST` request to the PHP middleware:
    *   **Endpoint:** `http://[::1]:4500/index.php/geturl` (or the configured PHP server IP)
    *   **Payload (Query Parameters):**
        *   `company_name`
        *   `bay_name`
        *   `ip1`, `username1`, `password1` (Encrypted)
        *   `ip2`, `username2`, `password2` (Optional)
        *   `ip3`, `username3`, `password3` (Optional)

### Step 2: PHP Generates Token
**Code Path:** `camera/application/controllers/Pages.php` -> `geturl()`
*   The PHP `geturl()` method receives the payload.
*   It validates that at least one camera IP and its corresponding credentials are provided.
*   It generates a unique token using `uniqid()`.
*   It inserts this record into the PHP MySQL database via `manage_cam_acess_model->insert_vehicle()`.
*   **Response:** It returns a JSON object to Odoo:
    `{"status": true, "token": "6abbaa7e24717", "url": "http://.../index.php/track/6abbaa7e24717"}`

### Step 3: Odoo Renders the iFrame
**Code Path:** `ac_ars_ip_camera/static/src/components/live_streaming/live_streaming.js`
*   Odoo receives the tracking URL from PHP.
*   The OWL widget (`ac_ars_camera_stream`) loads the URL inside an HTML `<iframe>` displayed to the user.

### Step 4: PHP Serves the Video Player
**Code Path:** `camera/application/controllers/Pages.php` -> `track($token)`
*   The browser iframe requests the `/track/{token}` URL.
*   PHP fetches the token record from MySQL, retrieves the encrypted camera credentials, and loads the `home.php` view.
*   `home.php` contains Javascript that connects to the local **Node.js Proxy** (`http://localhost:8088`).

### Step 5: Node.js Transcodes RTSP to HLS
**Code Path:** `camera/proxy/server.js`
*   The frontend JS sends the camera IPs and encrypted credentials to the Node.js server.
*   Node.js spawns an `ffmpeg` child process for each camera:
    `ffmpeg -rtsp_transport tcp -i rtsp://{user}:{pass}@{ip}:8080/cam/realmonitor?channel=1&subtype=0 -c:v copy -f hls stream1.m3u8`
*   `ffmpeg` continuously writes `.m3u8` and `.ts` chunk files to the `camera/streams/` directory.

### Step 6: Browser Plays the Stream
*   The `home.php` frontend uses `video.js` (and `videojs-http-streaming`) to fetch and play the generated `.m3u8` HLS playlist from the Node.js server.

### Step 7: Liveness Ping (Odoo Keep-Alive)
**Code Path:** `camera/assets/js/pingServer.js`
*   While the user watches the stream, `pingServer.js` repeatedly sends an HTTP `POST` to Odoo to indicate active viewing.
*   **Endpoint:** `/api/no_view_receive` (in `ac_ars_cc_camera/controllers/main.py`)
*   **Payload:** Raw JSON containing `"db": "kia_test"`, `"user": "kia@gmail.com"`, `"password": "kia"`, and `"token"`.
*   Odoo (via `request.get_json_data()`) authenticates the static API user, finds the active token, and updates `is_viewing = True` in the database.

---

## 3. Mandatory Database Fields
For Odoo to successfully initiate the stream, the `ac_ars_ip_camera` record MUST have:
*   `name` (IP Address)
*   `username` (RTSP Username)
*   `password` (RTSP Password)

If any of these are missing, the PHP `geturl()` endpoint will reject the request with:
`{"status": false, "message": "Unable to get any camera 1 Username/Password"}`

---

## 4. Odoo 18 Migration Notes (Troubleshooting)
*   **JSON-RPC vs Raw JSON:** In Odoo 18, `request.jsonrequest` was removed. For API endpoints like `/api/no_view_receive` that receive raw JSON payloads (instead of strictly formatted JSON-RPC 2.0 requests), you must use `request.get_json_data()`.
*   **Authentication Signature:** In Odoo 18, `request.session.authenticate()` requires a dictionary for credentials:
    `request.session.authenticate(db, {'login': user, 'password': password, 'type': 'password'})`.
*   **Hardcoded API Credentials:** The `pingServer.js` file contains hardcoded Odoo credentials used for the liveness ping. If the Odoo database name or user credentials change (e.g., deploying to production), this JS file MUST be manually updated.

## 5. Logs and Debugging
*   **PHP Errors:** Check `camera/application/logs/`. Fatal startup errors (like missing extensions) are output directly to the terminal running `php -S`.
*   **Node.js Errors:** Check the terminal running `node server.js`. If `ffmpeg` fails to connect to the RTSP stream, it will output `Connection refused` or `401 Unauthorized`.
*   **Odoo API Errors:** Check the Odoo server logs for exceptions on `/api/no_view_receive`.
