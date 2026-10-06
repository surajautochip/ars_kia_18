# Odoo 11 Resource Planner Flow: A Beginner's Guide

This document explains how the **Resource Planner** was designed in Odoo 11, how it drives the **Bay Planner**, and what we need to bring over to Odoo 18.

---

## 1. What is the Resource Planner?
In a busy service center, there are many **Bays** (locations where cars are fixed) and many **Technicians** (people who fix them). The Bay Planner is the visual UI (the drag-and-drop calendar), but the **Resource Planner** is the "brain" behind it.

The Resource Planner (`planner.calender` in Odoo 11) is a configuration model that tells the Bay Planner:
- **Which Bays** should be shown as columns on the screen?
- **Which Technicians** are available to be assigned to these bays?
- **What kind of jobs** (Repair Orders) should appear in the queue?

Without the Resource Planner configuration, the Bay Planner wouldn't know which bays to display or which technicians are working today.

---

## 2. Core Components & Architecture

### A. Resources (`resource.resource`)
Everything in the service center is treated as a "Resource". 
- **Bays** are created as resources with `resource_category = 'Bay'`.
- **Technicians** are created as resources with `resource_category = 'Technician'`.

### B. The Planner Calendar (`planner.calender`)
This is the central configuration record. A manager might create a "Mechanical Planner" and a "Bodyshop Planner".
- **`member_ids` (Resource)**: These are the Bays mapped to this planner. In the UI, these become the **Columns** in the calendar.
- **`resorce_pull_ids` (Resource Pull)**: These are the Technicians mapped to this planner. In the UI, these become the draggable chips in the **"Resource Pool"** sidebar.

### C. Repair Orders / Jobs
In Odoo 11, jobs were tracked via `sale.order` and `project.task`. If a job was unassigned, it appeared in the **Allocation Data (Unassigned Queue)** sidebar.

---

## 3. Data Flow Diagram

Here is a visual representation of how the data flows from the backend configuration to the frontend UI:

```mermaid
flowchart TD
    subgraph Backend Configuration
        RC[Resource Category\n(Bay / Technician)] --> R[Resource\n(resource.resource)]
        R -->|member_ids| PC[Planner Calendar\n(planner.calender)]
        R -->|resorce_pull_ids| PC
        SO[Repair Orders / Tasks\n(sale.order)] -.-> PC
    end

    subgraph Bay Planner UI
        PC -->|Dropdown Selection| UI_View[Select Planner View]
        UI_View -->|Loads member_ids| UI_Bays[Calendar Columns\n(Bays)]
        UI_View -->|Loads resorce_pull_ids| UI_Techs[Sidebar: Resource Pool\n(Technicians)]
        SO -->|Loads Unassigned| UI_Queue[Sidebar: Allocation Data\n(Vehicles/ROs)]
    end

    UI_Techs -->|Drag & Drop| UI_Bays
    UI_Queue -->|Drag & Drop| UI_Bays
```

---

## 4. The User Experience (Step-by-Step)

1. **Configuration (Backend):**
   - The Service Manager goes to *Resource Planner -> Resource Calendar*.
   - They create a new record called "General Service Planner".
   - They add Bay 1, Bay 2, and Bay 3 to the **Resource** tab (`member_ids`).
   - They add Tech John, Tech Mike, and Tech Sarah to the **Resource Pull** tab (`resorce_pull_ids`).

2. **Planning (Frontend):**
   - The Job Controller opens the **Bay Planner** UI.
   - At the top, they select "General Service Planner" from the dropdown.
   - The screen updates:
     - The **Calendar Grid** now shows Bay 1, Bay 2, Bay 3 as columns.
     - The **Resource Pool** (Right Sidebar) lists John, Mike, and Sarah.
     - The **Allocation Data** (Left Sidebar) lists all vehicles waiting for service.

3. **Allocation:**
   - The controller drags a Vehicle from the left sidebar and drops it onto Bay 1.
   - The controller drags "Tech John" from the right sidebar and drops him onto the Vehicle in Bay 1.
   - The system automatically creates a `calendar.event` (Odoo 11) linking the Vehicle, the Bay, and the Technician.

---

## 5. Odoo 18 Gap Analysis (What we have vs What we need)

To successfully port this to Odoo 18, we must bridge the gap between the old architecture and the new one.

### ✅ What is ALREADY AVAILABLE in Odoo 18:
- **The Frontend UI Structure:** The new Owl-based Bay Planner (`AC_BayPlanner.js`) successfully renders the calendar grid and the Unassigned Queue sidebar.
- **The Data Model for Jobs:** `ac.ars.allocation.data` has been created to replace the old `sale.order` dependency, holding the ROs for the queue.
- **Base Resources:** `resource.resource` still exists in Odoo 18.

### ❌ What is PENDING (Needs to be Implemented in Odoo 18):
1. **The `planner.calender` Model:** We need to recreate this model in Odoo 18. Currently, the Odoo 18 Bay Planner blindly fetches *all* resources. It needs a backend configuration to group them.
2. **The "Resource Pool" Sidebar:** The Odoo 18 frontend is missing the Technician sidebar. We need to fetch `resorce_pull_ids` and display them for drag-and-drop.
3. **The Dropdown Selector:** The frontend needs the top dropdown to let users switch between different planners (e.g., Mechanical vs Bodyshop).
4. **Linking Events:** When a technician and a vehicle are dropped into a bay, we need a mechanism to save this link (similar to `calendar.event` with `entry_type` in Odoo 11).

### Next Steps Recommendation
Before we can fully utilize the Bay Planner in Odoo 18, we must first recreate the `planner.calender` model and views from the `ac_rms` module so that the service center managers can configure their Bays and Technicians. Once that data exists, we can connect it to the Owl frontend.
