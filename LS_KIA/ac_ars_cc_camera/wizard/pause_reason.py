import base64
import logging
_logger = logging.getLogger(__name__)
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class DealerStreamingDetailsReport(models.TransientModel):
    _name = "streaming.pause"
    _description = "Live Streaming Pause Reason"

    reason_selection = fields.Selection([('waiting for approval', 'Waiting For Customer Approval'),
                                         ('waiting for parts', 'Waiting For Parts'),
                                         ('waiting for diagnosis', 'Waiting For Diagnosis'),
                                         ('waiting for decision', 'Waiting for Decision'),
                                         ('other', 'Other')], string='Reason')

    other_reason = fields.Text('Remark')
    ac_ars_live_stream_token_id = fields.Many2one('ac.ars.live.stream.token', default=lambda self: self.env.context.get('active_id'))

    
    def ac_ars_live_streaming_pause_wizard(self):
        _logger.info("Executing ac_ars_live_streaming_pause_wizard...")
        live_token = self.ac_ars_live_stream_token_id
        live_token.ac_ars_live_streaming_pause(self.reason_selection, self.other_reason)
