# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class PlannerCalendar(models.Model):
    _name = 'planner.calender'
    _description = 'Planner Calendar Configuration'

    name = fields.Char('Name', required=True)
    resource_category = fields.Many2one('resource.category', 'Resource Category')
    member_ids = fields.One2many('resource.resource', 'planner_calender_id', string='Resource (Bays)')
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)




class ResourceCategory(models.Model):
    _name = 'resource.category'
    _description = 'Resource Category'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    dashbord_name = fields.Char("Dashboard Name")
    alpr_is_bay = fields.Boolean('Is a Bay', default=False)
    is_dashbord = fields.Boolean(default=False)
    count_value = fields.Integer()

    def get_dahbord_data(self):
        _logger.info("Executing get_dahbord_data...")
        current_date = str(datetime.now().date())
        cr = self._cr
        cr.execute("""select count(distinct bl.vehicle_number) as count_value, rc.id from alpr_bay_vehicle_log bl INNER JOIN resource_resource rr on bl.bay_id = rr.id 
                    INNER JOIN resource_category rc on rr.resource_category = rc.id  where log_date ='""" + str(
            current_date) + """'group by rc.id""")
        dashbord_data = cr.dictfetchall()
        for data in dashbord_data:
            res_cat = self.env['resource.category'].search([('id', '=', data.get('id'))])
            update = res_cat.write(data)
            _logger.info(update)
            _logger.info(">>>>>>>>>>>>>>>>>>>>>", current_date, data)

    @api.model
    def get_vehicle_tracking_dashboard_data(self):
        current_date = str(datetime.now().date())
        # Fetch all dashboard bays
        categories = self.search([('is_dashbord', '=', True)])

        # Build base mapping
        result = []
        cat_map = {}
        for cat in categories:
            data_dict = {
                'id': cat.id,
                'dashbord_name': cat.dashbord_name or 'Unnamed Bay',
                'count_value': 0,
            }
            cat_map[cat.id] = data_dict
            result.append(data_dict)

        # Fetch counts
        cr = self._cr
        cr.execute("""
            SELECT count(distinct bl.vehicle_number) as count_value, rc.id 
            FROM alpr_bay_vehicle_log bl 
            INNER JOIN resource_resource rr on bl.bay_id = rr.id 
            INNER JOIN resource_category rc on rr.resource_category = rc.id  
            WHERE log_date = %s AND rc.is_dashbord = TRUE
            GROUP BY rc.id
        """, [current_date])

        counts = cr.dictfetchall()
        for count in counts:
            if count.get('id') in cat_map:
                cat_map[count.get('id')]['count_value'] = count.get('count_value')

        return result


class ResourceResourceExt(models.Model):
    _inherit = 'resource.resource'

    planner_calender_id = fields.Many2one('planner.calender', 'Planner Calendar (Bays)')
    resource_category = fields.Many2one('resource.category', 'Resource Category')



