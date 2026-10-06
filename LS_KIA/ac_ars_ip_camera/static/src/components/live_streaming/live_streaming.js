/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CameraStreamWidget extends Component {

    static template = "ac_ars_camera.camera_stream_widget";

    setup() {
        this.action = useService("action");
        const params = this.props.action.params || {};
        this.cameraId = params.camera_id;

        // Same state keys as before so the existing template keeps working
        this.state = useState({
            streamUrl:  "",
            error:      false,
            errorMsg:   "",
            loading:    true,
            bays:       [],
            fps:        15,
            activeView: "master",
            abrQuality: "medium",
            abrKbps:    0,
            url:        "",
        });

        onMounted(() => {
            const el = document.querySelector(".matrix-dashboard");
            const dialog = el?.closest(".modal");
            if (dialog) dialog.classList.add("live-stream-dialog");

            if (!this.cameraId) {
                this.state.error = true;
                this.state.errorMsg = "No camera selected.";
                this.state.loading = false;
                return;
            }

            // Odoo itself serves the MJPEG feed. No register / stop calls needed:
            // closing the dialog removes the <img>, the browser drops the
            // connection, and the server kills ffmpeg automatically.
            this.state.streamUrl =
                `/ac_ars_ip_camera/video_feed/${this.cameraId}` +
                `?quality=${this.state.abrQuality}&fps=${this.state.fps}&_t=${Date.now()}`;
            this.state.loading = false;
        });
    }

    selectView(view) {
        this.state.activeView = view;
    }

    stopAndClose() {
        // Clearing the src drops the connection immediately
        this.state.streamUrl = "";
        this.action.doAction({ type: "ir.actions.act_window_close" });
    }
}

registry.category("actions").add("ac_ars_camera_stream", CameraStreamWidget);