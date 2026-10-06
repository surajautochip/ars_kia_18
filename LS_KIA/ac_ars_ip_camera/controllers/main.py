import json
from odoo import fields, http
from odoo.tools import html_escape
from odoo.http import request
from hikvisionapi import Client
import os
import random

import logging

_logger = logging.getLogger(__name__)


class ip_camera_details(http.Controller):
    @http.route('/ip_camera/data', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def ip_camera_details(self, **kw):
        _logger.info("Executing ip_camera_details...")
        datas = []
        cam_data = []
        cam_records = request.env['camera.records'].sudo().search([('status', '=', 'recording')])
        recored_cam = request.env['camera.records'].sudo().search([('status', '=', 'processing')])
        if cam_records:
            for cam_record in cam_records:
                datas.append(cam_record.save_record())
                _logger.info(datas)
        if recored_cam:
            for record in recored_cam:
                cam_data.append(record.id)
        return datas, cam_data


class ip_camera_stop(http.Controller):
    @http.route('/ip_camera/stop', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def ip_camera_stop(self, **kw):
        _logger.info("Executing ip_camera_stop...")
        cam_data = []
        _logger.info(request.get_json_data())
        recored_cam = request.env['camera.records'].sudo().search([('status', '=', 'processing')])
        for rec_cam in recored_cam:
            cam_data.append(rec_cam.id)
            rec_cam.status = 'recorded'
        return cam_data


class ip_camera_start(http.Controller):
    @http.route('/ip_camera/start', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def ip_camera_start(self, **kw):
        _logger.info("Executing ip_camera_start...")
        _logger.info(request.get_json_data())

    @http.route('/ip_camera/status', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def ip_camera_details(self, order_id, **kw):
        _logger.info("Executing ip_camera_details...")
        res, camera_no = {}, 1
        order = request.env['sale.order'].browse(int(order_id.strip()))
        for camera in order.bay_id.ip_address:
            if camera.get_rtsp_url() and camera.test_connection():
                res.update({'status': True})
            elif 'status' in res and res['status']:
                res.update({'status': False,
                            'message': 'One camera could not able to access! Do you want to retry?'})
            else:
                res.update({'status': False,
                            'message': 'Camera could not able to access! Do you want to retry?'})
        return res

