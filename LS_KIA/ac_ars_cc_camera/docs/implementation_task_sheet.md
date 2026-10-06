# ARS Live Streaming (LS_KIA) - Implementation Tasks

- `[ ]` **Phase 1: Foundation & Cleanup**
  - `[ ]` Delete old Odoo 11 Python files from `LS_KIA/ars_cc_camera/models/`.
  - `[ ]` Create new `models/__init__.py`.
  - `[ ]` Create `security/ir.model.access.csv` with standard base access rights.

- `[ ]` **Phase 2: Core Models Migration (Infrastructure)**
  - `[ ]` Create `ac_ars_ip_camera.py` (`ac.ars.ip.camera`).
  - `[ ]` Create `ac_ars_cc_camera.py` (`ac.ars.cc.camera`).
  - `[ ]` Create `ac_ars_server_settings.py` (`ac.ars.live.streaming.settings`).
  - `[ ]` Create `ac_ars_server_status.py` (`ac.ars.server.status`).

- `[ ]` **Phase 3: Live Streaming Engine**
  - `[ ]` Create `ac_ars_live_streaming.py` (`ac.ars.live.streaming` & `ac.ars.live.streaming.line`).
  - `[ ]` Create `ac_ars_stream_token.py` (`ac.ars.live.stream.token`).
  - `[ ]` Refactor old SQL injection vulnerabilities into safe ORM calls.

- `[ ]` **Phase 4: Views & UI Modernization**
  - `[ ]` Create `views/menus.xml`.
  - `[ ]` Build `views/ac_ars_ip_camera_views.xml`.
  - `[ ]` Build `views/ac_ars_live_streaming_views.xml`.
  - `[ ]` Build `views/ac_ars_server_settings_views.xml`.

- `[ ]` **Phase 5: Final Testing & Deployment**
  - `[ ]` Update `__manifest__.py` with new model and view references.
  - `[ ]` Upgrade the `ars_cc_camera` module.
  - `[ ]` Validate module installs without traceback errors.
