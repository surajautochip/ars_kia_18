# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    evaluation_type = fields.Selection(
        [('online_api', 'Online Api'), ('local_req', 'Local Request')],
        'Identification Menthod', default='local_req', required=True)
    token = fields.Char('Token')
