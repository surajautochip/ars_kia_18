# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import fields, models, tools, api
from datetime import datetime, date
import calendar


class VehicleTrackingWizard(models.TransientModel):
	_name = 'vehicle.tracking.wizard'
	_description = "Vehicle Tracking Report Wizard"
	
	vehicle_number = fields.Char(string='Number Plate', required="True")

	
	def vehicle_tracking_report(self):
		data = {}
		self.env.cr.execute("""
			select
				  l.create_date as date
				, l.vehicle_number as vehicle_number
				, l.entry_type as entry_type
				, r.name as location
			from alpr_bay_vehicle_log l
			full outer join resource_resource r on r.id = l.bay_id

			where l.vehicle_number = '""" + str(self.vehicle_number) + """'
			group by l.create_date,l.vehicle_number,l.entry_type,r.name
		""")
		log_datas = sorted(self._cr.dictfetchall(), key = lambda i: i['date'])
		data.update({
			'reg_no': self.vehicle_number,
			'latest_datas': log_datas,
		})
		return self.env.ref('ars_auto_lpr.action_report_tracking').report_action([], data=data, config=False)