/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { useState } from "@odoo/owl";

export class CustomPasswordField extends CharField {
    static template = "ac_ars_ip_camera.CustomPasswordField";

    setup() {
        super.setup();
        this.state = useState({ showPassword: false });
    }

    togglePassword() {
        this.state.showPassword = !this.state.showPassword;
    }

    get inputType() {
        return this.state.showPassword ? "text" : "password";
    }

    get hasValue() {
        const val = this.props.record.data[this.props.name];
        return val !== false && val !== null && val !== undefined && val !== "";
    }

    get displayValue() {
        const val = this.props.record.data[this.props.name];
        if (val === false || val === null || val === undefined || val === "") {
            return "";
        }
        if (this.state.showPassword) {
            return String(val);
        }
        const len = String(val).length;
        return "•".repeat(Math.min(Math.max(len, 6), 12));
    }
}

export const customPasswordField = {
    ...charField,
    component: CustomPasswordField,
    displayName: "Custom Password",
    additionalClasses: ["o_field_custom_password"],
};

registry.category("fields").add("custom_password", customPasswordField);
