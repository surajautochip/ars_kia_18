# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
from datetime import datetime


class ResourceResource(models.Model):
    _inherit = 'resource.resource'
    resource_category = fields.Many2one('resource.category', 'Resource Category')

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


class AlprCamera(models.Model):
    _inherit = 'ac.ars.ip.camera'

    alpr_update_interval = fields.Float('Update Interval (Minute)', default=2, required=True)
    alpr_camera_url = fields.Char('Camera URL', compute='_get_ipaddress', store=1)
    alpr_bay_ids = fields.One2many('alpr.camera.bay', 'camera_id', string='Bay Mapping')
    hik_vision = fields.Boolean()

    @api.depends('name', 'http_port')
    def _get_ipaddress(self):
        _logger.info("Executing _get_ipaddress...")
        for obj in self:
            if obj.name and obj.http_port:
                obj.alpr_camera_url = obj.name + ":" + obj.http_port

    
    def save_bay_areas(self, areas):
        _logger.info("Executing save_bay_areas...")
        self.ensure_one()

        line_ids = {}
        for line in self.alpr_bay_ids:
            line_ids[line.bay_id.id] = line.id

        bay_data = []
        active_bay_ids = []
        for i, ar_data in areas.items():
            _bay_id = ar_data['bay_id']
            _bay_vals = {
                'bay_id': _bay_id,
                'disp_area_x': ar_data['disp_area_x'],
                'disp_area_y': ar_data['disp_area_y'],
                'disp_area_w': ar_data['disp_area_w'],
                'disp_area_h': ar_data['disp_area_h'],
                'disp_rel_area_x': ar_data['disp_rel_area_x'],
                'disp_rel_area_y': ar_data['disp_rel_area_y'],
                'disp_rel_area_w': ar_data['disp_rel_area_w'],
                'disp_rel_area_h': ar_data['disp_rel_area_h'],
            }
            active_bay_ids.append(_bay_id)
            if _bay_id in line_ids:
                bay_data += [[1, line_ids[_bay_id], _bay_vals]]
            else:
                bay_data += [[0, 0, _bay_vals]]

        for _bay_id in line_ids:
            if _bay_id not in active_bay_ids:
                bay_data += [[2, line_ids[_bay_id], ]]

        try:
            self.write({'alpr_bay_ids': bay_data})
        except:
            return False
        return True


class AlrpCameraBay(models.Model):
    _name = 'alpr.camera.bay'
    _description = 'Camera Bay Mapping'
    _rec_name = 'bay_id'

    camera_id = fields.Many2one('ac.ars.ip.camera', 'Camera', required=True)
    bay_id = fields.Many2one('resource.resource', 'Bay', required=True,
                             domain=[('resource_category.alpr_is_bay', '=', True)])
    disp_area_x = fields.Integer('Display Area X', required=True)
    disp_area_y = fields.Integer('Display Area Y', required=True)
    disp_area_w = fields.Integer('Display Area Width', required=True)
    disp_area_h = fields.Integer('Display Area Height', required=True)
    disp_area_string = fields.Char('Display Area', compute='_compute_display_area', store=False)
    disp_rel_area_x = fields.Integer('Display Relative Area X', required=True)
    disp_rel_area_y = fields.Integer('Display Relative Area Y', required=True)
    disp_rel_area_w = fields.Integer('Display Relative Area Width', required=True)
    disp_rel_area_h = fields.Integer('Display Relative Area Height', required=True)
    count_log = fields.Integer()
    is_bay_occupy = fields.Boolean("Is Occupy", default=False)

    _sql_constraints = [
        ('bay_uniq', 'unique(bay_id, camera_id)', 'Duplicate bays..!!'),
    ]

    
    @api.depends('disp_area_x', 'disp_area_y', 'disp_area_w', 'disp_area_h')
    def _compute_display_area(self):
        _logger.info("Executing _compute_display_area...")
        for rec in self:
            rec.disp_area_string = "%s:%s %sx%s" % (rec.disp_area_x, rec.disp_area_y, rec.disp_area_w, rec.disp_area_h)


class AlprBayVehicleLog(models.Model):
    _name = 'alpr.bay.vehicle.log'
    _description = 'Bay Vehicle Log'
    _order = 'id desc'

    vehicle_number = fields.Char('Number Plate', required=True)
    camera_id = fields.Many2one('ac.ars.ip.camera', 'Camera', required=True)
    bay_id = fields.Many2one('resource.resource', 'Location', required=True,
                             domain=[('resource_category.alpr_is_bay', '=', True)])
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'alpr.bay.vehicle.log'))
    entry_type = fields.Selection([('in', 'IN'), ('out', 'OUT')], default='in')
    log_date = fields.Date(string='Log Date')
    out_datetime = fields.Datetime('Out Date Time')
    date_update = fields.Datetime()
    is_created_log = fields.Boolean(string="Created Vehicle Log")


    # @api.depends('out_datetime')
    # def _compute_time(self):
    #     # duration = timedelta(0)
    #     for case in self:
    #         if case.out_datetime:
    #             start_time = datetime.datetime.strptime(case.stream_end_time, DEFAULT_SERVER_DATETIME_FORMAT)
    #             end_time = datetime.datetime.strptime(case.stream_start_time, DEFAULT_SERVER_DATETIME_FORMAT)
    #             duration = start_time - end_time
    #             case.streaming_duration = str(duration) + " min"

    
    def change_date(self):
        _logger.info("Executing change_date...")
        datas = self.env['alpr.bay.vehicle.log'].search([])
        for data in datas:
            if data.date_update:
                cr = self._cr
                cr.execute(
                    """update alpr_bay_vehicle_log set create_date = (select date_update from alpr_bay_vehicle_log where id = """ + str(data.id) + """) where id =""" + str(data.id))

class VehicleTrackingLog(models.Model):
    _name = 'vehicle.tracking.log'
    _description = 'Vehicle Tracking Log'
    _order = 'id desc'

    vehicle_number = fields.Char('Number Plate', required=True)
    start_time = fields.Datetime('Start Time')
    end_time = fields.Datetime('End Time')
    bay_id = fields.Many2one('resource.resource', 'Location', required=True,
                             domain=[('resource_category.alpr_is_bay', '=', True)])
    bay_type = fields.Many2one('resource.category', 'Location Type', required=True)
    company_id = fields.Many2one('res.company', 'Company')


    
    def create_vehicle_log(self):
        _logger.info("Executing create_vehicle_log...")
        bay_logs = self.env['alpr.bay.vehicle.log'].search([('is_created_log', '=', False)], order="id asc")
        for bay_log in bay_logs:
            bay_log.is_created_log = True
            if bay_log.vehicle_number != 'XXXX':
                vehicle_log = self.search([('vehicle_number', '=', bay_log.vehicle_number), ('bay_id', '=', bay_log.bay_id.id)])
                if not vehicle_log:
                    if bay_log.entry_type == 'in':
                        self.env['vehicle.tracking.log'].create({
                            'vehicle_number': bay_log.vehicle_number,
                            'start_time': bay_log.create_date,
                            'bay_id': bay_log.bay_id.id,
                            'bay_type': bay_log.bay_id.resource_category.id,
                            'company_id': bay_log.company_id.id,
                            })
                else:
                    if bay_log.entry_type == 'out':
                        vehicle_log.update({
                            'end_time': bay_log.create_date,
                            'company_id': bay_log.company_id.id,
                        })
                    if bay_log.entry_type == 'in':
                        vehicle_log.update({
                            'end_time': False,
                            'company_id': bay_log.company_id.id,
                        })