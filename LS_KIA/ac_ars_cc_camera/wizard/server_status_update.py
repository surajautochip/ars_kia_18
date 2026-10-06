from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class ServerStatusUpdate(models.TransientModel):
    _name = "live.stream.server.updation"

    is_cl_received = fields.Boolean(related="live_stream_sever.is_consent_letter_received")
    is_rollout_completed = fields.Boolean(related="live_stream_sever.is_rollout_completed")
    is_training_completed = fields.Boolean(related="live_stream_sever.is_training_completed")
    active_from = fields.Date(related="live_stream_sever.active_from")
    renewal_date = fields.Date(related="live_stream_sever.renewal_date")
    expiry_date = fields.Date(related="live_stream_sever.expiry_date")
    status_message = fields.Text()
    live_stream_sever = fields.Many2one('ac.ars.live.streaming.settings')
    company_id = fields.Many2one('res.company', related="live_stream_sever.company_id")
    edit_renewed_data = fields.Boolean()
    interval_number = fields.Integer(string='Renewed for', related='live_stream_sever.interval_number', default=1)
    interval_type = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('year', 'Year')],
        default='year', related='live_stream_sever.interval_type', required=True)

    ls_installation_status = fields.Selection([
        ('pending', 'Pending'),
        ('partially', 'Partially Completed'),
        ('completed', 'Completed')], default='pending', related='live_stream_sever.ls_installation_status')

    server_status = fields.Selection([
        ('inactive', 'Inactive'),
        ('active', 'Active'),
        ('expired', 'Expired')], default='inactive', related='live_stream_sever.server_status')

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("Executing create...")
        res = super(ServerStatusUpdate, self).create(vals_list)
        active_id = self.env.context.get('active_id')
        return res

    @api.onchange('renewal_date', 'active_from', 'interval_number')
    def get_expiry_date(self):
        _logger.info("Executing get_expiry_date...")
        if self.renewal_date:
            if self.interval_type == 'year':
                self.expiry_date = fields.Datetime.from_string(self.renewal_date) + relativedelta(
                    years=int(self.interval_number))
            elif self.interval_type == 'months':
                self.expiry_date = fields.Datetime.from_string(self.renewal_date) + relativedelta(
                    months=int(self.interval_number))
            elif self.interval_type == 'weeks':
                self.expiry_date = fields.Datetime.from_string(self.renewal_date) + timedelta(
                    weeks=int(self.interval_number))
            elif self.interval_type == 'days':
                self.expiry_date = fields.Datetime.from_string(self.renewal_date) + timedelta(
                    days=int(self.interval_number))
            elif self.interval_type == 'hours':
                self.expiry_date = fields.Datetime.from_string(self.renewal_date) + timedelta(
                    days=int(self.interval_number))

    @api.onchange('is_cl_received', 'is_rollout_completed', 'is_training_completed')
    def installation_status_updation(self):
        _logger.info("Executing installation_status_updation...")
        if not self.is_cl_received and self.is_rollout_completed and self.is_training_completed:
            self.ls_installation_status = 'partially'
        elif self.is_cl_received and self.is_rollout_completed and self.is_training_completed:
            self.ls_installation_status = 'completed'
        elif self.is_cl_received and self.is_rollout_completed or self.is_training_completed:
            self.ls_installation_status = 'partially'
        else:
            self.ls_installation_status = 'pending'
