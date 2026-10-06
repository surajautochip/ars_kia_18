/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, xml } from "@odoo/owl";

export class DashboardOWL extends Component {
    static template = xml`
        <div class="o_dashboard_legacy_wrapper p-4">
            <div class="alert alert-warning">
                <h3>ALPR Dashboard</h3>
                <p>This legacy dashboard is currently being migrated to Odoo 18 OWL. Full visual features will be available soon.</p>
            </div>
        </div>
    `;
}

registry.category("actions").add('ars_auto_lpr.main', DashboardOWL);
