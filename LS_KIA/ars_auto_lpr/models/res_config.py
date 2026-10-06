# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AlprNumplateConf(models.TransientModel):
	_name = 'alpr.config.settings'
	_inherit = 'res.config.settings'

	company_id = fields.Many2one('res.company', string='Institute', required=True, default=lambda self: self.env.company)
	evaluation_type = fields.Selection(
		[('online_api', 'Online Api'), ('local_req', 'Local Request')],
		'Identification Menthod', required=True, related='company_id.evaluation_type')
	token = fields.Char('Token', related='company_id.token')