# Implementation Plan: ARS Live Streaming (LS_KIA / Odoo 18 Modernization)

## Goal Description
The goal is to rebuild the Live Streaming and Camera Management system from scratch based on the team lead's new architecture in the `LS_KIA` directory. While we will follow the lead's modular architecture (keeping separate models for IP cameras, CC cameras, and server settings exactly as designed in Odoo 11), we will enforce modern **Odoo 18 professional standards**. This means all files, models, and XML IDs will be properly prefixed with `ac.ars.` to ensure global namespace safety and clean code structure.

## Proposed Model Architecture

Instead of lumping everything into one giant `live_streaming.py` file, we will break the models down professionally.

| Legacy Odoo 11 Model | New Odoo 18 Model (`ac.ars.` prefix) | Purpose |
| :--- | :--- | :--- |
| `ip.camera` | `ac.ars.ip.camera` | Stores IP camera details (IP, Port, Credentials). |
| `cc.camera` | `ac.ars.cc.camera` | Stores CC camera details (if applicable). |
| `live.streaming` | `ac.ars.live.streaming` | Core model tracking active streams, duration, and customer tokens. |
| `live.streaming.line` | `ac.ars.live.streaming.line` | Tracks individual viewing sessions for a specific stream. |
| `live.streaming.settings` | `ac.ars.live.streaming.settings` | Manages the edge FastAPI server IP, ports, and connection status per dealership. |
| `live.stream.server.status` | `ac.ars.server.status` | Logs historical uptime/downtime of the edge servers. |
| `live.stream.token` | `ac.ars.live.stream.token` | Generates secure streaming tokens for external API consumption. |

## Proposed File Architecture

```text
LS_KIA/ars_cc_camera/
├── __init__.py
├── __manifest__.py
├── docs/
│   ├── implementation_plan.md      <-- (This Document)
│   └── implementation_task_sheet.md 
├── models/
│   ├── __init__.py
│   ├── ac_ars_ip_camera.py         <-- (Replaces models.py/ip.camera)
│   ├── ac_ars_cc_camera.py         
│   ├── ac_ars_live_streaming.py    <-- (Replaces live_streaming.py)
│   ├── ac_ars_server_settings.py   <-- (Replaces live.streaming.settings)
│   ├── ac_ars_server_status.py     
│   ├── ac_ars_stream_token.py      <-- (Replaces live_stream_token.py)
│   └── ac_ars_allocation_data.py
├── views/
│   ├── ac_ars_ip_camera_views.xml
│   ├── ac_ars_live_streaming_views.xml
│   ├── ac_ars_server_settings_views.xml
│   └── menus.xml
└── security/
    └── ir.model.access.csv         <-- (Mandatory Odoo 18 Security Rules)
```

## Proposed Changes (Execution Phases)

### Phase 1: Foundation & Cleanup
1. **Clean Slate**: Delete the copy-pasted Odoo 11 python files from `LS_KIA/ars_cc_camera/models/` to remove the crash-causing code.
2. **Setup File Structure**: Create the new `ac_ars_` prefixed python files and their `__init__.py`.
3. **Security Rules**: Build the `ir.model.access.csv` to ensure Odoo 18 doesn't block the new models.

### Phase 2: Core Models Migration (Infrastructure)
1. **IP Camera**: Migrate `ip.camera` logic to `ac_ars_ip_camera.py`.
2. **Server Settings**: Migrate `live.streaming.settings` logic. Rewrite the raw `os.system("ping")` logic using modern Python `requests` and safe socket timeouts.

### Phase 3: Live Streaming Engine
1. **Live Streaming Models**: Migrate `live.streaming` and `live.streaming.line`.
2. **SQL Injection Removal**: Rewrite all raw `cr.execute()` queries in the `create` method of `live.streaming` into safe Odoo ORM `search()` methods.
3. **Token Management**: Migrate the `live.stream.token` logic for URL generation.

### Phase 4: Views & UI Modernization
1. **XML Rewrites**: Convert all old `<tree>` and `<form>` views to use Odoo 18 standard `<list>` tags and remove deprecated `view_type="form"` attributes.
2. **Menus**: Link the new views into a clean "Live Streaming" app menu.

## Verification Plan

### Automated/Manual Verification
- Restart the Odoo server and update `ars_cc_camera`.
- Verify the server starts cleanly with **0 Tracebacks** (no import errors, no XML parsing errors).
- Navigate to the UI and ensure the `ac.ars.ip.camera` and `ac.ars.live.streaming.settings` forms load correctly.
- Verify the security rules allow the admin user to create records.
