/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class BayPlanner extends Component {
    static template = "ac_ars_cc_camera.BayPlanner";
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.busService = useService("bus_service");
        this.gridScroll = useRef("gridScroll");
        this.headerScroll = useRef("headerScroll");
        
        this.onStreamUpdated = this.onStreamUpdated.bind(this);
        this.busService.addChannel("ac_ars_live_stream_channel");
        this.busService.subscribe("stream_updated", this.onStreamUpdated);
        
        onWillStart(async () => {
            await this.loadData();
        });
        
        this.state = useState({
            isQueueOpen: true,
            currentDate: new Date(),
            viewMode: "day", // 'day', '3days', 'week', 'month'
            planners: [],
            activePlannerId: null,
            bays: [],
            queueList: [],
            allocatedSlots: [],
            isDropdownOpen: false,
            isModalOpen: false,
            modalData: {
                bayId: null,
                startHourIndex: 0,
                reg: "",
                model: "",
                durationHours: 1,
                isEV: false
            },
            notifications: [],
            now: new Date()
        });

        onMounted(() => {
            this.updateCurrentTimeLine();
            
            setTimeout(() => this.autoScrollToNow(), 100);
        });

        onWillUnmount(() => {
            this.busService.unsubscribe("stream_updated", this.onStreamUpdated);
            if (this.animationFrameCurrentTimeLine) {
                cancelAnimationFrame(this.animationFrameCurrentTimeLine);
            }
        });
    }

    onStreamUpdated(payload) {
        if (payload && payload.id) {
            this.loadData();
        }
    }

    updateCurrentTimeLine() {
        const update = () => {
            const nextDate = new Date();
            if (nextDate.getSeconds() !== this.state.now.getSeconds()) {
                this.state.now = nextDate;
            }
            this.animationFrameCurrentTimeLine = requestAnimationFrame(update);
        };
        this.animationFrameCurrentTimeLine = requestAnimationFrame(update);
    }

    autoScrollToNow() {
        if (!this.gridScroll || !this.gridScroll.el) return;
        const container = this.gridScroll.el;
        
        const now = this.state.now;
        const d = new Date(this.state.currentDate);
        d.setHours(0, 0, 0, 0);
        
        let startOfView = new Date(d);
        if (this.state.viewMode === 'week') {
            startOfView.setDate(d.getDate() - d.getDay());
        }
        
        const diffMs = now.getTime() - startOfView.getTime();
        const dayOffset = Math.floor(diffMs / 86400000);
        const hourOffset = now.getHours() + now.getMinutes() / 60 - 8;
        
        let leftPos = 0;
        if (dayOffset >= 0 && hourOffset >= 0) {
            leftPos = (dayOffset * 22 * 120) + (hourOffset * 2 * 120);
        }
        
        // Scroll so the indicator is roughly in the first third of the view
        const scrollPos = Math.max(0, leftPos - 200);
        container.scrollTo({ left: scrollPos, behavior: 'smooth' });
    }

    async loadData() {
        const d = new Date(this.state.currentDate);
        let startDate = new Date(d);
        let endDate = new Date(d);

        if (this.state.viewMode === '3days') {
            endDate.setDate(d.getDate() + 2);
        } else if (this.state.viewMode === 'week') {
            const dayOfWeek = d.getDay();
            startDate.setDate(d.getDate() - dayOfWeek);
            endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 6);
        } else if (this.state.viewMode === 'month') {
            startDate.setDate(1);
            startDate.setDate(startDate.getDate() - startDate.getDay()); // Sunday of first week
            const endDateActual = new Date(d.getFullYear(), d.getMonth() + 1, 0);
            if (endDateActual.getDay() !== 6) {
                endDateActual.setDate(endDateActual.getDate() + (6 - endDateActual.getDay()));
            }
            endDate = endDateActual;
        }
        
        const targetStart = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}-${String(startDate.getDate()).padStart(2, '0')}`;
        const targetEnd = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, '0')}-${String(endDate.getDate()).padStart(2, '0')}`;
        
        try {
            const data = await this.orm.call(
                "ac.ars.allocation.data",
                "get_bay_planner_data",
                [targetStart, targetEnd, this.state.activePlannerId || null]
            );
            
            this.state.planners = data.planners || [];
            this.state.activePlannerId = data.active_planner_id || null;
            this.state.bays = data.bays || [];
            this.state.queueList = [];
            this.state.allocatedSlots = [];

            const baseDateOnly = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()).getTime();

            data.allocations.forEach(rec => {
                let startColumnIndex = 0;
                let durationColumns = 1;
                let durationHours = 1;
                
                if (rec.date_start && rec.date_end) {
                    const tStart = new Date(rec.date_start.replace(' ', 'T') + 'Z');
                    const tEnd = new Date(rec.date_end.replace(' ', 'T') + 'Z');
                    
                    const startFloat = tStart.getHours() + (tStart.getMinutes() / 60);
                    durationHours = (tEnd.getTime() - tStart.getTime()) / (1000 * 60 * 60);
                    if (durationHours <= 0) durationHours = 1;
                    
                    if (this.state.viewMode === 'month') {
                        const recDateOnly = new Date(tStart.getFullYear(), tStart.getMonth(), tStart.getDate()).getTime();
                        const dayDiff = Math.floor((recDateOnly - baseDateOnly) / 86400000);
                        
                        let hourOffset = startFloat - 8;
                        if (hourOffset < 0) hourOffset = 0;
                        if (hourOffset > 10) hourOffset = 10;
                        
                        startColumnIndex = dayDiff + (hourOffset / 10);
                        durationColumns = durationHours / 10;
                    } else {
                        // day, 3days, week are half-hourly views (22 intervals/day)
                        const recDateOnly = new Date(tStart.getFullYear(), tStart.getMonth(), tStart.getDate()).getTime();
                        const dayDiff = Math.floor((recDateOnly - baseDateOnly) / 86400000);
                        
                        startColumnIndex = (dayDiff * 22) + ((startFloat - 8) * 2);
                        durationColumns = durationHours * 2;
                    }
                    
                    if (startColumnIndex < 0) startColumnIndex = 0;
                    if (durationColumns < 0.2) durationColumns = 0.5; // At least one half-hour block
                }

                const slot = {
                    id: rec.id,
                    bayId: rec.bay_id,
                    reg: rec.reg,
                    model: rec.model,
                    status: rec.status,
                    startColumnIndex: startColumnIndex,
                    durationColumns: durationColumns,
                    durationHours: durationHours,
                    slotDate: (rec.date_start ? new Date(rec.date_start.replace(' ', 'T') + 'Z').setHours(0,0,0,0) : 0),
                    isEV: false
                };

                if (rec.status === 'queue' || !rec.bay_id || !rec.date_start) {
                    this.state.queueList.push(slot);
                } else {
                    this.state.allocatedSlots.push(slot);
                }
            });
        } catch (error) {
            console.error("Failed to load bay planner data:", error);
        }
    }

    get filteredBays() {
        return this.state.bays;
    }

    getAllocatedSlotsForBay(bayId) {
        return this.state.allocatedSlots.filter(s => s.bayId === bayId);
    }

    isBayLive(bayId) {
        return this.state.allocatedSlots.some(s => s.bayId === bayId && s.status === 'live');
    }

    get liveStreamsCount() {
        const activeBayIds = this.state.bays.map(b => b.id);
        return this.state.allocatedSlots.filter(s => s.status === 'live' && activeBayIds.includes(s.bayId)).length;
    }

    async applyPlannerFilter(plannerId) {
        this.state.activePlannerId = parseInt(plannerId);
        this.state.isDropdownOpen = false;
        await this.loadData();
    }
    
    toggleDropdown() {
        this.state.isDropdownOpen = !this.state.isDropdownOpen;
    }

    // --- Action Router for Live Streams List ---
   openLiveStreamsList() {
        const activeBayIds = this.state.bays.map(b => b.id);
        const liveAllocationIds = this.state.allocatedSlots
            .filter(s => s.status === 'live' && activeBayIds.includes(s.bayId))
            .map(s => parseInt(s.id))
            .filter(id => !isNaN(id));
        this.action.doAction({
            name: "Current LS Data",
            type: "ir.actions.act_window",
            res_model: "ac.ars.live.stream.token",
            views: [[false, "list"], [false, "form"]],
            domain: [["dms_ro_number", "in", liveAllocationIds]],
            target: "current"
        });
    }

    get activeBayName() {
        const planner = this.state.planners.find(p => p.id === this.state.activePlannerId);
        return planner ? planner.name : 'Select a Planner';
    }

    // --- COMPUTED / DYNAMIC TIMELINE ---
    get formattedDate() {
        const d = this.state.currentDate;
        const opts = { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' };
        return d.toLocaleDateString('en-US', opts);
    }

    get timeColumns() {
        const cols = [];
        const baseDate = new Date(this.state.currentDate);
        baseDate.setHours(0, 0, 0, 0);

        if (this.state.viewMode === 'day') {
            const startHour = 8;
            for (let i = 0; i < 22; i++) {
                const totalMinutes = (startHour * 60) + (i * 30);
                const h = Math.floor(totalMinutes / 60);
                const m = totalMinutes % 60;
                const ampm = h >= 12 ? 'PM' : 'AM';
                const hr12 = h > 12 ? h - 12 : (h === 0 ? 12 : h);
                cols.push({
                    label: m === 0 ? `${hr12.toString().padStart(2, '0')}:00 ${ampm}` : `${hr12.toString().padStart(2, '0')}:30 ${ampm}`,
                    subLabel: ""
                });
            }
        } else if (this.state.viewMode === '3days') {
            const startHour = 8;
            for (let d = 0; d < 3; d++) {
                const currentDate = new Date(baseDate);
                currentDate.setDate(baseDate.getDate() + d);
                for (let i = 0; i < 22; i++) {
                    const totalMinutes = (startHour * 60) + (i * 30);
                    const h = Math.floor(totalMinutes / 60);
                    const m = totalMinutes % 60;
                    const ampm = h >= 12 ? 'PM' : 'AM';
                    const hr12 = h > 12 ? h - 12 : (h === 0 ? 12 : h);
                    cols.push({
                        label: m === 0 ? `${hr12.toString().padStart(2, '0')}:00 ${ampm}` : `${hr12.toString().padStart(2, '0')}:30 ${ampm}`,
                        subLabel: currentDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
                    });
                }
            }
        } else if (this.state.viewMode === 'week') {
            const dayOfWeek = baseDate.getDay();
            const startOfWeek = new Date(baseDate);
            startOfWeek.setDate(baseDate.getDate() - dayOfWeek);
            const startHour = 8;
            
            for (let d = 0; d < 7; d++) {
                const currentDate = new Date(startOfWeek);
                currentDate.setDate(startOfWeek.getDate() + d);
                for (let i = 0; i < 22; i++) {
                    const totalMinutes = (startHour * 60) + (i * 30);
                    const h = Math.floor(totalMinutes / 60);
                    const m = totalMinutes % 60;
                    const ampm = h >= 12 ? 'PM' : 'AM';
                    const hr12 = h > 12 ? h - 12 : (h === 0 ? 12 : h);
                    cols.push({
                        label: m === 0 ? `${hr12.toString().padStart(2, '0')}:00 ${ampm}` : `${hr12.toString().padStart(2, '0')}:30 ${ampm}`,
                        subLabel: currentDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
                    });
                }
            }
        } else if (this.state.viewMode === 'month') {
            const year = baseDate.getFullYear();
            const month = baseDate.getMonth();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            for (let i = 1; i <= daysInMonth; i++) {
                cols.push({
                    label: `${i}`,
                    subLabel: baseDate.toLocaleDateString('en-US', { month: 'short' })
                });
            }
        }
        return cols;
    }

    get currentTimeStr() {
        if (!this.state.now) return '';
        const now = this.state.now;
        const hr12 = now.getHours() % 12 || 12;
        const mins = now.getMinutes().toString().padStart(2, '0');
        const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
        return `${hr12.toString().padStart(2, '0')}:${mins} ${ampm}`;
    }

    get currentMonthYear() {
        if (!this.state.currentDate) return '';
        const d = new Date(this.state.currentDate);
        return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    }

    get nowIndicatorStyle() {
        if (!this.state.now) return "display: none;";
        
        const now = this.state.now;
        const d = new Date(this.state.currentDate);
        d.setHours(0, 0, 0, 0);
        
        if (this.state.viewMode === 'month') {
            return "display: none;";
        }
        
        let startOfView = new Date(d);
        if (this.state.viewMode === 'week') {
            startOfView.setDate(d.getDate() - d.getDay());
        }
        
        const diffMs = now.getTime() - startOfView.getTime();
        const dayOffset = Math.floor(diffMs / 86400000);
        const hourOffset = now.getHours() + now.getMinutes() / 60 - 8;
        
        let maxDays = 1;
        if (this.state.viewMode === '3days') maxDays = 3;
        if (this.state.viewMode === 'week') maxDays = 7;
        
        if (dayOffset >= 0 && dayOffset < maxDays && hourOffset >= 0 && hourOffset <= 11) {
            const leftPos = (dayOffset * 22 * 120) + (hourOffset * 2 * 120);
            return `left: ${leftPos}px;`;
        }
        
        return "display: none;";
    }

    get currentWeekRange() {
        if (!this.state.currentDate) return '';
        const base = new Date(this.state.currentDate);
        const dayOfWeek = base.getDay();
        const startOfWeek = new Date(base);
        startOfWeek.setDate(base.getDate() - dayOfWeek);
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);
        
        const startMonth = startOfWeek.toLocaleDateString('en-US', { month: 'short' });
        const endMonth = endOfWeek.toLocaleDateString('en-US', { month: 'short' });
        const startDay = startOfWeek.getDate();
        const endDay = endOfWeek.getDate();
        const year = endOfWeek.getFullYear(); // Use end of week year
        
        if (startMonth === endMonth) {
            return `${startMonth} ${startDay} - ${endDay}, ${year}`;
        } else {
            return `${startMonth} ${startDay} - ${endMonth} ${endDay}, ${year}`;
        }
    }

    get weekDays() {
        if (this.state.viewMode !== 'week') return [];
        const base = new Date(this.state.currentDate);
        const dayOfWeek = base.getDay();
        const startOfWeek = new Date(base);
        startOfWeek.setDate(base.getDate() - dayOfWeek);
        const days = [];
        for (let i = 0; i < 7; i++) {
            const d = new Date(startOfWeek);
            d.setDate(startOfWeek.getDate() + i);
            days.push({
                dateObj: new Date(d),
                label: d.toLocaleDateString('en-US', { weekday: 'short' }),
                dateLabel: `${d.getMonth() + 1}/${d.getDate()}`,
                isToday: new Date().toDateString() === d.toDateString()
            });
        }
        return days;
    }

    get weekTimeSlots() {
        // 12am to 11pm = 24 hour slots (matches screenshot)
        const slots = [];
        for (let h = 0; h < 24; h++) {
            const ampm = h >= 12 ? 'pm' : 'am';
            const hr12 = h === 0 ? 12 : (h > 12 ? h - 12 : h);
            slots.push({ hour: h, label: `${hr12}${ampm}` });
        }
        return slots;
    }

    getWeekSlotsForDayAndHour(dayIndex, hour) {
        if (this.state.viewMode !== 'week') return [];
        const base = new Date(this.state.currentDate);
        const dayOfWeek = base.getDay();
        const startOfWeek = new Date(base);
        startOfWeek.setDate(base.getDate() - dayOfWeek);
        const targetDay = new Date(startOfWeek);
        targetDay.setDate(startOfWeek.getDate() + dayIndex);
        const targetDayTime = new Date(targetDay).setHours(0, 0, 0, 0);

        return this.state.allocatedSlots.filter(s => {
            if (s.slotDate !== targetDayTime) return false;
            // Check if slot starts in this hour
            const slotDayOffset = Math.floor(s.startColumnIndex / 22);
            if (slotDayOffset !== dayIndex) return false;
            
            const slotStartHourFloat = 8 + ((s.startColumnIndex % 22) / 2);
            return Math.floor(slotStartHourFloat) === hour;
        }).map(s => {
            const slotStartHourFloat = 8 + ((s.startColumnIndex % 22) / 2);
            const topOffset = Math.round((slotStartHourFloat - Math.floor(slotStartHourFloat)) * 48) + 2;
            const height = Math.round(s.durationHours * 48) - 4;
            return {
                ...s,
                styleTop: `${topOffset}px`,
                styleHeight: `${height}px`
            };
        });
    }

    get monthGrid() {
        if (this.state.viewMode !== 'month') return [];
        
        const baseDate = new Date(this.state.currentDate);
        const year = baseDate.getFullYear();
        const month = baseDate.getMonth();
        
        const firstDay = new Date(year, month, 1);
        
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay()); // Sunday
        
        const grid = [];
        const d = new Date(startDate);
        const todayTime = new Date().setHours(0,0,0,0);
        
        while (grid.length < 42) { // 6 weeks * 7 days
            const dayTime = d.getTime();
            const isCurrentMonth = d.getMonth() === month;
            
            // Get allocations for this day
            const allocations = this.state.allocatedSlots.filter(s => s.slotDate === dayTime);
            
            grid.push({
                dateObj: new Date(d),
                dayNum: d.getDate(),
                isCurrentMonth: isCurrentMonth,
                allocations: allocations,
                isToday: dayTime === todayTime
            });
            
            d.setDate(d.getDate() + 1);
        }
        return grid;
    }

    async shiftDate(offset) {
        const d = new Date(this.state.currentDate);
        if (this.state.viewMode === 'day') {
            d.setDate(d.getDate() + offset);
        } else if (this.state.viewMode === '3days') {
            d.setDate(d.getDate() + (offset * 3));
        } else if (this.state.viewMode === 'week') {
            d.setDate(d.getDate() + (offset * 7));
        } else if (this.state.viewMode === 'month') {
            d.setMonth(d.getMonth() + offset);
        }
        this.state.currentDate = d;
        await this.loadData();
    }

    async resetToday() {
        this.state.currentDate = new Date();
        await this.loadData();
    }

    async setViewMode(mode) {
        this.state.viewMode = mode;
        await this.loadData();
    }

    toggleQueue() {
        this.state.isQueueOpen = !this.state.isQueueOpen;
    }

    syncScroll(ev) {
        if (this.headerScroll.el && this.gridScroll.el) {
            this.headerScroll.el.scrollLeft = this.gridScroll.el.scrollLeft;
        }
    }

    // --- Drag and Drop Handlers ---
    onDragStartQueue(ev, item) {
        ev.dataTransfer.setData("text/plain", JSON.stringify({ type: 'queue', id: item.id }));
        ev.dataTransfer.effectAllowed = "move";
    }

    onDragStartGrid(ev, slotId, bayId) {
        ev.dataTransfer.setData("text/plain", JSON.stringify({ type: 'grid', id: slotId, sourceBayId: bayId }));
        ev.dataTransfer.effectAllowed = "move";
    }

    async onDropGrid(ev, bayId, colIndex) {
        ev.preventDefault();
        const dataStr = ev.dataTransfer.getData("text/plain");
        if (!dataStr) return;
        
        try {
            const data = JSON.parse(dataStr);
            if (data.type === 'queue') {
                const itemIdx = this.state.queueList.findIndex(q => String(q.id) === String(data.id));
                if (itemIdx !== -1) {
                    const item = this.state.queueList[itemIdx];
                    
                    // Backend persistence
                    if (typeof item.id === 'number') {
                        const dateStart = this._getUtcDateStringFromColumn(colIndex, 0);
                        const dateEnd = this._getUtcDateStringFromColumn(colIndex, parseFloat(item.durationHours) || 2);
                        await this.orm.write("ac.ars.allocation.data", [item.id], {
                            resource_id: parseInt(bayId),
                            state: 'scheduled',
                            date_start: dateStart,
                            date_end: dateEnd
                        });
                    }

                    this.state.queueList.splice(itemIdx, 1);
                    this.state.allocatedSlots.push({
                        id: item.id,
                        bayId: bayId,
                        reg: item.reg,
                        model: item.model,
                        service: "Scheduled Maintenance",
                        startColumnIndex: colIndex,
                        durationColumns: this.state.viewMode === 'month' ? ((parseFloat(item.durationHours) || 2) / 10) : ((parseFloat(item.durationHours) || 2) * 2),
                        durationHours: parseFloat(item.durationHours) || 2,
                        status: "scheduled",
                        isEV: item.isEV
                    });
                }
            } else if (data.type === 'grid') {
                const slotIdx = this.state.allocatedSlots.findIndex(s => String(s.id) === String(data.id));
                if (slotIdx !== -1) {
                    // Backend persistence
                    if (typeof data.id === 'number') {
                        const slot = this.state.allocatedSlots[slotIdx];
                        const dateStart = this._getUtcDateStringFromColumn(colIndex, 0);
                        const dateEnd = this._getUtcDateStringFromColumn(colIndex, slot.durationHours);
                        await this.orm.write("ac.ars.allocation.data", [data.id], {
                            resource_id: parseInt(bayId),
                            date_start: dateStart,
                            date_end: dateEnd
                        });
                    }
                    
                    this.state.allocatedSlots[slotIdx].bayId = bayId;
                    this.state.allocatedSlots[slotIdx].startColumnIndex = colIndex;
                }
            }
        } catch (err) {
            console.error("Drop parsing error", err);
        }
    }

    removeAllocation(slotId) {
        const idx = this.state.allocatedSlots.findIndex(s => String(s.id) === String(slotId));
        if (idx !== -1) {
            const removed = this.state.allocatedSlots.splice(idx, 1)[0];
            this.state.queueList.push({
                id: "u_" + Date.now(),
                reg: removed.reg,
                model: removed.model,
                durationHours: removed.durationHours,
                ref: "S-RETURN",
                priority: "NORMAL",
                isEV: removed.isEV
            });
            this.addNotification(`Removed allocation for ${removed.reg}`);
        }
    }

    async toggleStreamStatus(slotId, newStatus) {
        const slot = this.state.allocatedSlots.find(s => s.id === slotId);
        if (slot) {
            // Optimistic UI update
            slot.status = newStatus === 'resume' ? 'live' : newStatus;
            
            // Backend persistence
            let recordId = parseInt(slotId);
            if (!isNaN(recordId)) {
                try {
                    if (newStatus === 'live') {
                        await this.orm.call("ac.ars.allocation.data", "action_start_broadcast", [[recordId]]);
                    } else if (newStatus === 'resume') {
                        await this.orm.call("ac.ars.allocation.data", "action_resume_broadcast", [[recordId]]);
                    } else {
                        await this.orm.write("ac.ars.allocation.data", [recordId], {
                            state: newStatus
                        });
                    }
                } catch (e) {
                    console.error("Failed to update stream status", e);
                }
            } else {
                console.warn("Skipping backend update for unsaved record ID:", slotId);
            }
        }
    }

    // --- Modal Handlers ---
    async openFeed(bayId) {
        try {
            // Fetch the camera linked to this bay
            const bayInfo = await this.orm.searchRead(
                "resource.resource",
                [["id", "=", parseInt(bayId)]],
                ["ip_address"]
            );
            
            if (bayInfo.length > 0 && bayInfo[0].ip_address.length > 0) {
                const cameraId = bayInfo[0].ip_address[0];
                const cameraInfo = await this.orm.searchRead(
                    "ac.ars.ip.camera",
                    [["id", "=", cameraId]],
                    ["cam_name", "rtsp_url"]
                );

                if (cameraInfo.length > 0) {
                    this.action.doAction({
                        type: 'ir.actions.client',
                        tag: 'ac_ars_camera_stream',
                        target: 'new',
                        params: {
                            camera_id: cameraInfo[0].id,
                            stream_url: cameraInfo[0].rtsp_url,
                            title: cameraInfo[0].cam_name,
                        },
                    });
                } else {
                    this.addNotification("Camera details not found for this bay.");
                }
            } else {
                this.addNotification("No camera configured for this bay.");
            }
        } catch(e) {
            console.error("Failed to open camera feed", e);
            this.addNotification("Failed to open camera feed.");
        }
    }

    addNotification(message) {
        const id = Date.now();
        this.state.notifications.push({ id, message });
        setTimeout(() => {
            const idx = this.state.notifications.findIndex(n => n.id === id);
            if (idx !== -1) {
                this.state.notifications.splice(idx, 1);
            }
        }, 3000);
    }

    openAllocationModal(bayId, colIndex, existingSlot = null) {
        if (existingSlot) {
            this.state.modalData = {
                bayId: bayId,
                startColumnIndex: colIndex !== undefined ? colIndex : existingSlot.startColumnIndex,
                queueItemId: existingSlot.id,
                durationHours: existingSlot.durationHours,
                specialist: ""
            };
        } else {
            this.state.modalData = {
                bayId: bayId || (this.state.bays.length > 0 ? this.state.bays[0].id : ""),
                startColumnIndex: colIndex !== undefined ? colIndex : 0, // default
                queueItemId: "",
                durationHours: 2,
                specialist: ""
            };
        }
        this.state.isModalOpen = true;
    }

    openAssignModal(item) {
        this.state.modalData = {
            bayId: this.state.bays.length > 0 ? this.state.bays[0].id : "",
            startColumnIndex: 0, // default
            queueItemId: item.id,
            durationHours: parseFloat(item.durationHours) || 2,
            specialist: ""
        };
        this.state.isModalOpen = true;
    }

    closeAllocationModal() {
        this.state.isModalOpen = false;
    }

    async confirmAllocation() {
        const data = this.state.modalData;
        if (!data.bayId) return;

        let reg = "Manual Entry";
        let model = "Unknown";
        let isEV = false;
        
        let qItemIndex = -1;
        if (data.queueItemId) {
            qItemIndex = this.state.queueList.findIndex(q => String(q.id) === String(data.queueItemId));
            if (qItemIndex !== -1) {
                const item = this.state.queueList[qItemIndex];
                reg = item.reg;
                model = item.model;
                isEV = item.isEV;
                
                // Backend persistence if needed
                if (typeof item.id === 'number') {
                    try {
                        const dateStart = this._getUtcDateStringFromColumn(data.startColumnIndex, 0);
                        const dateEnd = this._getUtcDateStringFromColumn(data.startColumnIndex, parseFloat(data.durationHours) || 2);
                        await this.orm.write("ac.ars.allocation.data", [item.id], {
                            resource_id: parseInt(data.bayId),
                            state: 'scheduled',
                            date_start: dateStart,
                            date_end: dateEnd
                        });
                    } catch (e) { console.error(e); }
                }
                
                // Remove from queue
                this.state.queueList.splice(qItemIndex, 1);
            } else {
                // If it's not in the queue, check if it's already an allocated slot (Reschedule flow)
                const aItemIndex = this.state.allocatedSlots.findIndex(a => String(a.id) === String(data.queueItemId));
                if (aItemIndex !== -1) {
                    const item = this.state.allocatedSlots[aItemIndex];
                    reg = item.reg;
                    model = item.model;
                    isEV = item.isEV;
                    
                    // Backend persistence
                    if (typeof item.id === 'number') {
                        try {
                            const dateStart = this._getUtcDateStringFromColumn(data.startColumnIndex, 0);
                            const dateEnd = this._getUtcDateStringFromColumn(data.startColumnIndex, parseFloat(data.durationHours) || 2);
                            await this.orm.write("ac.ars.allocation.data", [item.id], {
                                resource_id: parseInt(data.bayId),
                                date_start: dateStart,
                                date_end: dateEnd
                            });
                        } catch (e) { console.error(e); }
                    }
                    
                    // Remove old allocation from array so we can push the new one
                    this.state.allocatedSlots.splice(aItemIndex, 1);
                }
            }
        }

        this.state.allocatedSlots.push({
            id: data.queueItemId ? data.queueItemId : "a_" + Date.now(),
            bayId: parseInt(data.bayId) || data.bayId,
            reg: reg,
            model: model,
            service: "Scheduled Maintenance",
            startColumnIndex: parseFloat(data.startColumnIndex),
            durationColumns: this.state.viewMode === 'month' ? ((parseFloat(data.durationHours) || 2) / 10) : ((parseFloat(data.durationHours) || 2) * 2),
            durationHours: parseFloat(data.durationHours) || 2,
            status: "scheduled",
            isEV: isEV
        });
        
        const bayName = this.state.bays.find(b => b.id == data.bayId)?.name || 'BAY';
        this.addNotification(`Assigned ${reg} to ${bayName}`);
        
        this.closeAllocationModal();
    }

    _getUtcDateStringFromColumn(colIndex, duration = 0) {
        const d = new Date(this.state.currentDate);
        if (this.state.viewMode === 'month') {
            let startDate = new Date(d);
            startDate.setDate(1);
            d.setTime(startDate.getTime());
            d.setDate(d.getDate() + parseInt(colIndex));
            
            const durHrs = parseFloat(duration) || 0;
            startDate.setHours(8 + Math.floor(durHrs), (durHrs % 1) * 60, 0, 0);
            d.setTime(startDate.getTime());
        } else {
            let startDate = new Date(d);
            if (this.state.viewMode === 'week') {
                startDate.setDate(d.getDate() - d.getDay());
            }
            // For day, 3days, week: colIndex is in half-hours (22 intervals per day)
            const dayOffset = Math.floor(colIndex / 22);
            const halfHourOffset = colIndex % 22;
            startDate.setDate(startDate.getDate() + dayOffset);
            
            const startHour = 8 + Math.floor(halfHourOffset / 2);
            const startMin = (halfHourOffset % 2) * 30;
            
            const durHrs = parseFloat(duration) || 0;
            const durTotalMins = durHrs * 60;
            
            startDate.setHours(startHour, startMin + durTotalMins, 0, 0);
            d.setTime(startDate.getTime());
        }
        return d.toISOString().replace('T', ' ').substring(0, 19);
    }
}

registry.category("actions").add("ac_ls_bay_planner", BayPlanner);
