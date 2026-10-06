# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api, _
from odoo.exceptions import UserError


class BayStatusReport(models.AbstractModel):
    _name = 'report.ars_auto_lpr.report_bay_status'

    @api.model
    def get_report_values(self, docids, data=None):
        _logger.info("Executing get_report_values...")
        res = {
            'doc_ids': docids,
            'data': data,
        }
        return res