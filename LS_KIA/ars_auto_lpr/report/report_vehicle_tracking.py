# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class VehicleTrackingReport(models.AbstractModel):
	_name = 'report.ars_auto_lpr.report_vehicle_tracking'

	@api.model
	def get_report_values(self, docids, data=None):
		_logger.info("Executing get_report_values...")
		if not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))

		model = self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_id'))
		res = {
			'doc_ids': docids,
			'doc_model': model,
			'data': data,
			'docs': docs,
		}
		return res