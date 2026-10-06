# PHP Live Streaming – Functional Flow Guide

This guide explains how the Live Streaming feature works from a user's perspective, starting from camera configuration to actually viewing the live stream in the Odoo interface.

---

## 1. Camera Configuration (Prerequisites)
Before a user can view a live stream, the cameras must be correctly configured in Odoo.

**Where to configure:**
*   Navigate to the **IP Cameras** setup menu in Odoo (usually under `Live Streaming > IP Cameras` or tied to specific Service Bays).

**Required Fields:**
For a camera to stream successfully, the following fields are **MANDATORY**:
1.  **IP Address**: The physical network IP of the camera (e.g., `192.168.1.100`).
2.  **Username**: The login username for the camera's RTSP feed (e.g., `admin`).
3.  **Password**: The login password for the camera's RTSP feed.

*Note: If any of these three fields are missing or typed incorrectly, the system will not be able to connect to the camera, and the Live Stream will fail to load.*

---

## 2. Opening the Live Stream

### Step 1: The User Clicks "Live Streaming"
When a user opens an ongoing Service/Allocation record and clicks the **Live Streaming** button, Odoo immediately gathers the camera configurations tied to that specific bay.

### Step 2: Odoo Asks PHP for a Secure Link
Odoo securely packages the camera's IP, Username, and Password (up to 3 cameras) and sends them to the external PHP Application. 
*   **Why PHP?** The PHP application acts as a secure middleman. It stores the request, generates a temporary, secure "Tracking URL", and gives this URL back to Odoo.

### Step 3: The Video Player Opens
Odoo receives the Tracking URL from PHP and opens it inside a popup window or an embedded frame (iFrame) directly within the Odoo interface. 
*   At this point, the user sees the Live Streaming interface loading.

---

## 3. How the Video Actually Plays

Once the Odoo interface loads the PHP Tracking URL, the following background process happens instantly:

1.  **PHP Connects to the Node.js Server:** The PHP tracking page silently tells a local Node.js streaming server (running on port 8088) to start fetching the video.
2.  **Node.js Connects to the Camera:** The Node.js server uses a tool called `ffmpeg` to log into the physical IP Camera using the Username and Password configured in Step 1.
3.  **Video Translation (Transcoding):** IP Cameras use a video format called "RTSP" that web browsers cannot play directly. Node.js translates this RTSP video into a browser-friendly format called "HLS".
4.  **Playback:** The PHP tracking page fetches this translated HLS video and plays it on your screen.

*Summary: The browser does NOT connect directly to the camera. The flow is: **Camera → Node.js Server → PHP Page → User's Browser**.*

---

## 4. The "Ping" (Keeping the Stream Alive)

While the user is watching the video, the PHP page needs to tell Odoo "Hey, the user is still watching!".

*   Every few seconds, the Javascript running on the video page sends a **Ping** (a silent network request) back to Odoo (`/api/no_view_receive`).
*   This ping contains a hardcoded database name, username, and password to authenticate itself with Odoo.
*   This tells Odoo to update the "Viewing Status" of that record to `Active/True`.

---

## 5. Troubleshooting Common Failures

If the Live Stream does not load, or shows a spinning circle, here is what goes wrong:

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **"Unable to get camera Username/Password"** | The IP Camera record in Odoo is missing the IP, Username, or Password. | Edit the Camera record in Odoo and fill in all mandatory fields. |
| **Video player loads but stays black or spins forever** | The Node.js proxy server is either offline, or the camera is unreachable. | 1. Ensure `node server.js` is running.<br>2. Ensure the Camera is powered on and reachable on the network. |
| **Odoo terminal shows "psycopg2.OperationalError"** | The `pingServer.js` file is trying to log into the wrong Odoo database (e.g., `ARS` instead of `kia_test`). | The Javascript file must be updated to point to the correct test/live database. |
| **Odoo terminal shows "Login failed" or "Access Denied"** | The `pingServer.js` file has outdated login credentials (username/password) hardcoded. | Update `pingServer.js` with the correct Odoo login credentials and do a Hard Refresh (`Ctrl + F5`) in your browser. |
