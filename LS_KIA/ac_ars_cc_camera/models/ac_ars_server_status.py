# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class AcArsServerStatus(models.Model):
    _name = 'ac.ars.live.stream.server.status'
    _description = 'Server Status'

    name = fields.Char('Name')
    offline_datetime = fields.Datetime()
    duration = fields.Char()
    last_online = fields.Datetime()
    day_diff = fields.Integer()
    send_mail = fields.Boolean()
    port_status = fields.Selection([('online', 'Became Online'), ('offline', 'Offline'),('in_progress','In Progress')])
    live_server_id = fields.Many2one('ac.ars.live.streaming.settings')
    server_type =  fields.Selection([('cloud','Cloud'),('on_premise', 'On Premise')])

    def automate_mail_sent(self):
        _logger.info("Executing automate_mail_sent...")
        template_id = self.env.ref('ac_ars_cc_camera.server_status_automate_email').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def send_server_status_email(self):
        _logger.info("Executing send_server_status_email...")
        template_id = self.env.ref('ac_ars_cc_camera.server_status_list_email').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def get_dealership_detail(self):
        _logger.info("Executing get_dealership_detail...")
        data = []
        live_id = self.env['ac.ars.live.streaming.settings'].search([('port_status', '=', 'offline')])
        for ls in live_id:
            ss_obj = ls.server_status_ids.search(
                [('id', 'in', ls.server_status_ids.ids), ('port_status', '=', 'offline')], order='id desc', limit=1)
            ls_data = [ls.name, ls.company_id.name, ss_obj.offline_datetime, ss_obj.duration]
            data.append(ls_data)
        return data

    def get_server_status(self):
        _logger.info("Executing get_server_status...")
        current_dt = fields.Datetime.now()
        start_time = self.offline_datetime
        if not start_time:
            return self
        date_count = current_dt - start_time
        self.duration = str(date_count)
        if date_count.days >= 2 and self.day_diff != date_count.days:
            self.day_diff = date_count.days
            if self.live_server_id.email:
                self.automate_mail_sent()
        return self
