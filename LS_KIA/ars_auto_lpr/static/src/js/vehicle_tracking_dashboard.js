/** @odoo-module */

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class VehicleTrackingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        this.state = useState({
            bays: []
        });

        onWillStart(async () => {
            await this.fetchData();
        });
    }

    async fetchData() {
        try {
            const data = await this.orm.call('resource.category', 'get_vehicle_tracking_dashboard_data', []);
            if (data) {
                this.state.bays = data;
            }
        } catch (e) {
            console.error("Error fetching Vehicle Tracking Dashboard data", e);
        }
    }
}

VehicleTrackingDashboard.template = "ars_auto_lpr.VehicleTrackingDashboard";
registry.category("actions").add("ars_auto_lpr.tracking_dashboard_main", VehicleTrackingDashboard);
