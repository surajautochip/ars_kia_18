/** @odoo-module **/

import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class StatusDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        this.state = useState({
            company_count: [],
            zone_count: [],
            area_count: [],
            state_count: [],
            manager_count: [],
            tpsm_count: [],
        });

        this.graphs = {};

        onWillStart(async () => {
            await loadJS("https://cdn.jsdelivr.net/npm/apexcharts");

            this.state.company_count = await this.orm.call("ac.ars.live.streaming", "get_count", []);
            this.state.zone_count = await this.orm.call("ac.ars.live.streaming", "get_zone_count", []);
            this.state.area_count = await this.orm.call("ac.ars.live.streaming", "get_area_count", []);
            this.state.state_count = await this.orm.call("ac.ars.live.streaming", "get_state_count", []);
            this.state.manager_count = await this.orm.call("ac.ars.live.streaming", "get_manager_count", []);
            this.state.tpsm_count = await this.orm.call("ac.ars.live.streaming", "get_tpsm_count", []);

            this.graphs.company_graph = await this.orm.call("ac.ars.live.streaming", "get_company_count_graph", []);
            this.graphs.zone_graph = await this.orm.call("ac.ars.live.streaming", "get_zone_count_graph", []);
            this.graphs.area_graph = await this.orm.call("ac.ars.live.streaming", "get_area_count_graph", []);
            this.graphs.state_graph = await this.orm.call("ac.ars.live.streaming", "get_state_count_graph", []);
            this.graphs.manager_graph = await this.orm.call("ac.ars.live.streaming", "get_manager_count_graph", []);
            this.graphs.tpsm_graph = await this.orm.call("ac.ars.live.streaming", "get_tpsm_count_graph", []);
        });

        onMounted(() => {
            this.renderPieChart("company-wise-archievement", this.graphs.company_graph, "India Wise Archievement");
            this.renderPieChart("zone-wise-archievement", this.graphs.zone_graph[0] || [], "Zones Archievement");
            this.renderPieChart("area-wise-archievement", this.graphs.area_graph[0] || [], "Areas Archievement");
            this.renderPieChart("state-wise-archievement", this.graphs.state_graph[0] || [], "States Archievement");
            this.renderPieChart("manager-wise-archievement", this.graphs.manager_graph[0] || [], "Managers Archievement");
            this.renderPieChart("tpsm-wise-archievement", this.graphs.tpsm_graph[0] || [], "TPSM Archievement");
        });
    }

    renderPieChart(elementId, graphData, titleText) {
        if (!graphData || graphData.length === 0) return;
        const series = graphData.map(d => d.y);
        const labels = graphData.map(d => d.name);
        
        const options = {
            chart: { type: 'pie', height: 350 },
            series: series,
            labels: labels,
            title: { text: titleText }
        };
        const el = document.querySelector("#" + elementId);
        if (el) {
            const chart = new ApexCharts(el, options);
            chart.render();
        }
    }

    async openAction(model, method, kwargs) {
        const company_count = await this.orm.call(model, method, [], { kwargs: kwargs });
        this.action.doAction({
            name: "Company",
            type: "ir.actions.act_window",
            res_model: "res.partner",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [["id", "in", company_count]],
        });
    }

    // Company
    clickCompany(id) { this.openAction("ac.ars.live.streaming", "show_total_company", {id: id}); }

    // Zone
    clickZoneTotal(zone) { this.openAction("ac.ars.live.streaming", "show_total_zone", {zone: zone}); }
    clickZoneStreaming(zone, c_td) { this.openAction("ac.ars.live.streaming", "show_total_streaming_zone", {zone: zone, c_td: c_td}); }

    // Area
    clickAreaTotal(area) { this.openAction("ac.ars.live.streaming", "show_total_area", {area: area}); }
    clickAreaStreaming(area, c_td) { this.openAction("ac.ars.live.streaming", "show_total_streaming_area", {area: area, c_td: c_td}); }

    // State
    clickStateTotal(state) { this.openAction("ac.ars.live.streaming", "show_total_state", {state: state}); }
    clickStateStreaming(state, c_td) { this.openAction("ac.ars.live.streaming", "show_total_streaming_state", {state: state, c_td: c_td}); }

    // Manager
    clickManagerTotal(manager) { this.openAction("ac.ars.live.streaming", "show_total_manager", {manager: manager}); }
    clickManagerStreaming(manager, c_td) { this.openAction("ac.ars.live.streaming", "show_total_streaming_manager", {manager: manager, c_td: c_td}); }

    // TPSM
    clickTpsmTotal(tpsm) { this.openAction("ac.ars.live.streaming", "show_total_tpsm", {tpsm: tpsm}); }
    clickTpsmStreaming(tpsm, c_td) { this.openAction("ac.ars.live.streaming", "show_total_streaming_tpsm", {tpsm: tpsm, c_td: c_td}); }
}

StatusDashboard.template = "ac_ars_status_dashboard.StatusDashboard";
registry.category("actions").add("ac_ars_status_dashboard_client_action", StatusDashboard);
