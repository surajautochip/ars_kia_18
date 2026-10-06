/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class LiveStreamDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            company: "",
            dealer_code: "",
            today: "",
            month: "",
            mtd: { total: 0, viewed: 0, not_viewed: 0, rate: 0 },
            lmtd: { total: 0, viewed: 0, not_viewed: 0, rate: 0 },
            change: { total: "0%", viewed: "0%", not_viewed: "0%", rate: "0%" },
            bar_months: [],
            cameras: { total: 0, online: 0, offline: 0, list: [] },
            utilization: { stream_hours: 0, cam_utilization_pct: 0, bay_list: [] },
            loading: true,
            syncing: false,
            optionValue: "28",
        });

        onWillStart(async () => {
            await this.fetchDashboardData();
        });
    }

    async fetchDashboardData() {
        if (!this.state.loading) { this.state.syncing = true; }
        this.state.loading = this.state.loading || false;
        try {
            const result = await this.orm.call(
                "ac.ars.live.streaming",
                "get_dashboard_stats",
                []
            );
            if (result) {
                this.state.company = result.company || "";
                this.state.dealer_code = result.dealer_code || "";
                this.state.today = result.today || "";
                this.state.month = result.month || "";
                this.state.mtd = result.mtd || { total: 0, viewed: 0, not_viewed: 0, rate: 0 };
                this.state.lmtd = result.lmtd || { total: 0, viewed: 0, not_viewed: 0, rate: 0 };
                this.state.change = result.change || { total: "0%", viewed: "0%", not_viewed: "0%", rate: "0%" };
                this.state.bar_months = result.bar_months || [];
                this.state.cameras = result.cameras || { total: 0, online: 0, offline: 0, list: [] };
                this.state.utilization = result.utilization || { stream_hours: 0, cam_utilization_pct: 0, bay_list: [] };
            }
        } finally {
            this.state.loading = false;
            this.state.syncing = false;
        }
    }

    
    async refreshCamera(camId) {
        if (!camId) return;
        this.state.syncing = true;
        try {
            const status = await this.orm.read('ac.ars.ip.camera', [camId], ['status']);
            if (status && status.length > 0) {
                const cam = this.state.cameras.list.find(c => c.id === camId);
                if (cam) {
                    cam.status = status[0].status;
                    this.state.cameras.online = this.state.cameras.list.filter(c => c.status === 'online').length;
                    this.state.cameras.offline = this.state.cameras.list.filter(c => c.status === 'offline').length;
                }
            }
        } catch (e) {
            console.error('Error refreshing camera:', e);
        } finally {
            this.state.syncing = false;
        }
    }

    isPositiveChange(changeStr) {
        return changeStr && changeStr.startsWith("+");
    }

    async actionTotalLinkSent() {
        const domain = await this.orm.call(
            "ac.ars.live.streaming",
            "show_total_link_sent",
            [this.state.optionValue]
        );
        this.action.doAction({
            name: "Total Links Sent",
            res_model: "ac.ars.live.streaming",
            views: [[false, "list"], [false, "form"]],
            type: "ir.actions.act_window",
            view_mode: "list",
            domain: domain,
        });
    }

    async actionCustomerViewed() {
        const domain = await this.orm.call(
            "ac.ars.live.streaming",
            "show_customer_viewed_record",
            [this.state.optionValue]
        );
        this.action.doAction({
            name: "Customer Viewed Records",
            res_model: "ac.ars.live.streaming",
            views: [[false, "list"], [false, "form"]],
            type: "ir.actions.act_window",
            view_mode: "list",
            domain: domain,
        });
    }

    async actionCustomerNotViewed() {
        const domain = await this.orm.call(
            "ac.ars.live.streaming",
            "show_customer_not_viewed_record",
            [this.state.optionValue]
        );
        this.action.doAction({
            name: "Customer Not Viewed Records",
            res_model: "ac.ars.live.streaming",
            views: [[false, "list"], [false, "form"]],
            type: "ir.actions.act_window",
            view_mode: "list",
            domain: domain,
        });
    }

    getBarHeightStyle(count) {
        const max = Math.max(...(this.state.bar_months.map(m => m.count)), 1);
        const pct = Math.round((count / max) * 80) + 5;
        return `height: ${pct}%`;
    }
}

LiveStreamDashboard.template = "ac_ars_live_stream_dashboard.LiveStreamDashboard";

registry.category("actions").add("ac_ls_dashboard", LiveStreamDashboard);