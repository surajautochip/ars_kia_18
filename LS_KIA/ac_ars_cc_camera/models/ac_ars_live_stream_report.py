# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class AcArsLiveStreamReport(models.Model):
    _name = 'ac.ars.live.stream.daily.report'
    _description = 'Live Stream Daily Report'

    company_id = fields.Many2one('res.company', "Dealer Name")
    date = fields.Date("Date")
    link_sent = fields.Integer("Total link sent to customer")
    viewed_link = fields.Integer("Customer viewed link")
    not_viewed_link = fields.Integer("Customer not viewed link")
    total_no_bay = fields.Integer("Total number of BAY")
    camera_ids = fields.Many2many("ac.ars.ip.camera", string="Cameras")
    tot_cus_viewed_time = fields.Char('Total Customer Viewed Time')
    tot_stream_time = fields.Char('Total Streaming Time')
    offline_duration = fields.Char('Offline Duration')
