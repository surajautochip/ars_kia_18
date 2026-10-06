# DMS to Odoo Live Streaming SSO Authentication Flow

This document outlines the functional and technical architecture of the Single Sign-On (SSO) integration between the Dealer Management System (DMS) and the Odoo Live Streaming application. It covers the current secure implementation by the Lead Developer and the next steps required to finalize the user experience.

---

## 1. Functional Overview

From a functional perspective, this integration ensures a seamless and secure transition for users moving from the DMS into the Odoo Live Streaming portal. 

* **Seamless Access:** When a dealer is logged into the DMS and clicks the link to open Live Streaming, they are immediately logged into Odoo without having to remember or enter a separate Odoo username and password.
* **Strict Data Isolation:** The system automatically identifies which dealership the user belongs to. Upon entering Odoo, the dealer's view is securely restricted so they only see Cameras, Live Streams, and Dashboard data belonging to their specific dealership branch.
* **Enhanced Security:** Instead of relying on static passwords that could be intercepted, the system relies on dynamic tokens generated during the active session.

---

## 2. Technical Overview: Current Implementation

The Lead Developer has implemented a highly secure provisioning API (`/dms/token/custom/login`) that replaces the legacy, insecure methods used in Odoo 11.

### Legacy Method (Odoo 11) vs Modern Method (Odoo 18)
* **Odoo 11 Method:** The previous implementation often passed the user's raw password directly through the URL parameters (`/web/logins?password=...`) to force a login. This is a severe security vulnerability.
* **Odoo 18 Method:** The new implementation completely abandons password-based logins for DMS users. Instead, it uses a token-based handshake.

### How the Provisioning API Works
When the DMS server calls `/dms/token/custom/login`, it passes a payload containing the user's ID (`dms_uid`), the Dealer Code (`d_code`), and a secure `incoming_token`.

1. **Company Mapping:** Odoo searches for the `res.company` that matches the provided Dealer Code.
2. **User Identification:** Odoo checks if a user with that `dms_uid` already exists.
3. **Secure User Creation:** If the user does not exist, they are dynamically created. To prevent manual backdoor access, their Odoo password is set to a cryptographically secure, randomized 32-byte string (`secrets.token_urlsafe(32)`). Since no one knows this password, the user can *only* log in via the SSO flow.
4. **Token Storage:** The `incoming_token` is saved to the user's record as `dms_token`.
5. **Role Assignment:** The method `ls_set_user_permission()` is called to automatically assign the correct Odoo security groups (Access Rights) to the user.

---

## 3. Technical Overview: Next Steps for Implementation

While the current API successfully provisions the user and stores the secure token in the database, it **does not initiate a web browser session**. To complete the SSO flow, we need to implement a Landing Controller and verify the Record Rules.

### Phase 1: The Landing Controller
We need to build a new HTTP controller (e.g., `/dms/landing/redirect`) that acts as the entry point for the user's browser.

1. **URL Structure:** The DMS will redirect the user's browser to `https://odoo-server/dms/landing/redirect?uid=123&token=ABCxyz`.
2. **Validation:** The controller will query the `res.users` table for a record where `dms_uid == uid` and `dms_token == token`.
3. **Session Establishment:** If a match is found, the controller will explicitly inject the user's ID into the Odoo session (`request.session.uid = user.id`), securely bypassing the password check.
4. **Redirection:** Finally, the controller will redirect the user to the standard Odoo backend (`/web`), where they will land on the Live Streaming Dashboard.

### Phase 2: Data Isolation (Record Rules)
Once the user is authenticated, we must guarantee they can only see their own dealership's data.

1. **Multi-Company Security:** We will review the `security.xml` files for the Camera (`ac.ars.ip.camera`) and Live Streaming (`ac.ars.live.streaming`) models.
2. **Rule Verification:** We will ensure that robust multi-company Record Rules (`ir.rule`) are in place. For example, applying a domain like `['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]`.
3. **Result:** Because the provisioning API successfully links the user to their specific `company_id`, the Odoo ORM will automatically apply these Record Rules. If a dealer from "Branch A" logs in, the ORM will silently filter out all cameras and streams belonging to "Branch B" at the database level.
