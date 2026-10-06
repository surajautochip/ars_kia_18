# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
from datetime import datetime
import json
import requests
from difflib import SequenceMatcher
import re


def similar(a, b):
    _logger.info("Executing similar...")
    return SequenceMatcher(None, a, b).ratio()


pattern = "^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$"
patten2 = "^[A-Z]{2}[0-9][A-Z][A-Z]{2}[0-9]{4}$"
patten3 = "^[A-Z]{2}[0-9][A-Z]{2}[0-9]{4}$"


class AlrpOnlineServer(models.Model):
    _name = 'alpr.server.online'
    _description = 'Alpr Online Server'
    _rec_name = 'bay_name'

    bay_name = fields.Char('Bay Name')
    bay_id = fields.Integer('Bay Id')
    camera_id = fields.Integer('Camera Id')
    date_time = fields.Datetime()
    image = fields.Binary('Image')
    plate = fields.Char('Vehicle Number')
    entry_type = fields.Selection([('in', 'IN'), ('out', 'OUT')], default='in')
    is_retrived = fields.Boolean("Retrived", default=False)
    company_id = fields.Many2one('res.company', string='Company', help="Company Name")
    disp_area_x1 = fields.Integer(required=True)
    disp_area_y1 = fields.Integer(required=True)
    disp_area_x2 = fields.Integer(required=True)
    disp_area_y2 = fields.Integer(required=True)
    disp_area_string = fields.Char('Display Area', compute='_compute_display_area', store=False)

    
    @api.depends('disp_area_x1', 'disp_area_y1', 'disp_area_x2', 'disp_area_y2')
    def _compute_display_area(self):
        _logger.info("Executing _compute_display_area...")
        for rec in self:
            rec.disp_area_string = "%s:%s %sx%s" % (
                rec.disp_area_x1, rec.disp_area_y1, rec.disp_area_x2, rec.disp_area_y2)

    def validate_and_create_log(self, cam_obj, encoded_string):
        _logger.info("Executing validate_and_create_log...")
        response = []
        online_server = self.env['alpr.server.online']
        dealer_code = cam_obj['req_type'][0]['dealer_code']
        company_id = self.env['res.company'].search([('dealer_code', '=', dealer_code)], limit=1)
        result = online_server.Online_License_Plate_Recognition(cam_obj, encoded_string)
        for res in result:
            bay_id = res['bay_id']
            vehicle_number = res['plate']
            log_recs = online_server.search([('bay_id', '=', bay_id)], order='id desc', limit=1)
            if re.match(pattern, vehicle_number) or re.match(patten2, vehicle_number) or re.match(patten3,
                                                                                                  vehicle_number):
                if len(log_recs) > 0 and log_recs[0].plate[-4:] == vehicle_number[-4:]:
                    if log_recs[0].entry_type == 'out':
                        log_recs[0].unlink()
                    response += [{
                        'status': False,
                        'title': 'Oops! Something went wrong',
                        'message': 'Vehicle ' + log_recs[0].plate + ' Already In The BAY ' + log_recs[
                            0].bay_name,
                    }]
                    return response
                else:
                    res.update({
                        "company_id": company_id.id
                    })
                    bay_log = online_server.search([('plate', '=', vehicle_number)], order='id desc', limit=1)
                    if len(bay_log) > 0 and bay_log[0].entry_type != 'out':
                        _logger.info("<<<<<<<<<< Out Entry Creating >>>>>>>>>>>")
                        out_entry = bay_log[0].copy()
                        out_entry.write(
                            {'type': 'out', 'date_time': fields.Datetime.from_string(fields.Datetime.now())})
                    _logger.info("New Entry Created >>>>>>>>>>>>>")
                    online_server.create(res)
                    response += [{
                        'plate': res['plate'],
                        'bay_id': res['bay_id'],
                        'cam_id': res['camera_id'],
                        'type': 'in'
                    }]
        return response

    def Find_Out_Bay(self, cam_obj, alpr_api_response):
        _logger.info("Executing Find_Out_Bay...")
        data = False
        for bay_obj in cam_obj['bays']:
            bay_inside = False
            for alpr_obj in alpr_api_response['results']:
                alpr_x1 = alpr_obj['coordinates'][0]['x'] if 'coordinates' in alpr_obj else alpr_obj['box']['xmin']
                alpr_y1 = alpr_obj['coordinates'][0]['y'] if 'coordinates' in alpr_obj else alpr_obj['box']['ymin']
                alpr_x2 = alpr_obj['coordinates'][2]['x'] if 'coordinates' in alpr_obj else alpr_obj['box']['xmax']
                alpr_y2 = alpr_obj['coordinates'][2]['y'] if 'coordinates' in alpr_obj else alpr_obj['box']['ymax']
                num_plate = alpr_obj['plate'].upper()
                if (alpr_x1 > bay_obj['x1'] * 2.42) and (alpr_y1 > bay_obj['y1'] * 2.42):
                    if (alpr_x2 < bay_obj['x2'] * 2.42) and (alpr_y2 < bay_obj['y2'] * 2.42):
                        bay_inside = True
                        data = []
                        val = {'bay_id': bay_obj['bay_id'],
                               'bay_name': bay_obj['bay_name'],
                               'camera_id': cam_obj['camera_id'],
                               'plate': num_plate,
                               'entry_type': 'in',
                               'disp_area_y2': bay_obj['y2'],
                               'disp_area_x2': bay_obj['x2'],
                               'disp_area_y1': bay_obj['y1'],
                               'disp_area_x1': bay_obj['x1'],
                               'date_time': fields.Datetime.from_string(fields.Datetime.now())
                               }
                        data += [val]
                        # _logger.info(bay_obj['bay_name'],bay_obj['is_bay_occupy'],num_plate)
                if bay_inside == False:
                    _logger.info("//////Bay Inside False///////\n", alpr_obj['plate'].upper())
            return (data)

    def Online_License_Plate_Recognition(self, cam_obj, encoded_string):
        _logger.info("Executing Online_License_Plate_Recognition...")
        _logger.info("\nOnline License Plate Recognition\n")
        regions = ['in']
        SECRET_KEY = self.env.company.token
        base64_image = encoded_string
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            data=dict(regions=regions, upload=base64_image),  # Optional
            headers={'Authorization': 'Token ' + SECRET_KEY})
        # p_logger.info(response.json())
        alpr_api_response = response.json()
        if 'results' in alpr_api_response:
            result = self.Find_Out_Bay(cam_obj, alpr_api_response)
        else:
            _logger.info("______||||Error While Calling Online ALPR||||______\n", alpr_api_response)
            result = alpr_api_response
        return (result)
