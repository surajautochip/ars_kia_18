/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";

export class BookingStageMaskField extends Component {
    setup() {
        this.user = useService("user");
        this.isAdmin = false;
        onWillStart(async () => {
            this.isAdmin = await this.user.hasGroup("base.group_system");
        });
    }
}

BookingStageMaskField.template = "ac_ars_ip_camera.BookingStageMaskField";
BookingStageMaskField.props = {
    ...standardFieldProps,
};
BookingStageMaskField.supportedTypes = ["char"];

registry.category("fields").add("booking_stage_mask", {
    component: BookingStageMaskField,
});
