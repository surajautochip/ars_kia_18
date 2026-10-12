# -*- coding: utf-8 -*-

import json
from odoo import fields, http
from odoo.tools import html_escape
from odoo.http import request
from hikvisionapi import Client
import os
import random
from datetime import datetime
import logging
import re
import threading
import httplib2

_logger = logging.getLogger(__name__)

API_FIELDS = {
    'bay': ['disp_area_x', 'disp_area_y', 'disp_area_w', 'disp_area_h', 'disp_rel_area_x', 'disp_rel_area_y',
            'disp_rel_area_w', 'disp_rel_area_h']
}


class AlprBaySettingsDashboard(http.Controller):

    @http.route('/ars_auto_lpr_bay_dashboard/data', type='json', auth='user')
    def alpr_bay_settings_data(self, **kw):
        _logger.info("Executing alpr_bay_settings_data...")

        bays = {}
        company = request.env.company.id
        alpr_bay_ids = request.env['resource.resource'].search(
            [('id', '>', 0), ('resource_category.alpr_is_bay', '=', True), ('company_id', '=', company)])

        for bay in alpr_bay_ids:
            bays[bay.id] = {
                'name': bay.name,
            }

        cameras = {}
        camera_ids = request.env['ac.ars.ip.camera'].search(
            [('id', '>', 0), ('hik_vision', '=', True), ('company_id', '=', company)])
        for camera in camera_ids:
            _t_cc_name = "(%s)" % (camera.cam_name) if camera.cam_name else ''
            cameras[camera.id] = {
                'name': "%s %s" % (camera.name, _t_cc_name),
                'camera_url': request.httprequest.host_url + 'ars_auto_lpr/static/src/bay_images/' + str(
                    camera.id) + '.jpg?rand=' + str(random.randint(0, 1000)),
                'bays': {},
            }
            for bay in camera.alpr_bay_ids:
                _b_data = bay.read(API_FIELDS['bay'])[0]
                _b_data['bay_id'] = bay.bay_id.id
                if 'id' in _b_data:
                    del _b_data['id']
                cameras[camera.id]['bays'][bay.bay_id.id] = _b_data
        res = {
            'bays': bays,
            'cameras': cameras,
        }
        return res

    @http.route('/ars_auto_lpr/get_camera_data/<string:camera_id>', type='json', auth='user')
    def alpr_get_camera_data(self, camera_id=None, **kw):
        _logger.info("Executing alpr_get_camera_data...")
        camera = {}
        camera_rec = request.env['ac.ars.ip.camera'].search([('id', '=', int(camera_id))])
        # cam = Client("http://" + camera_rec.alpr_camera_url, camera_rec.user_name, camera_rec.password, timeout=30)
        # cam.count_events = 2  # The number of events we want to retrieve (default = 1)
        # response = cam.Streaming.channels[102].picture(method='get', type='opaque_data')
        pic_url = ("http://"+camera_rec.alpr_camera_url+"/ISAPI/Streaming/channels/101/picture")
        # admin, Zebra01!
        h = httplib2.Http()
        h.add_credentials(camera_rec.user_name, camera_rec.password)  # Basic authentication
        resp, content = h.request(pic_url, "GET")
        with open(
                '/opt/odoo/ac-hyundai-projects/ars_auto_lpr/static/src/bay_images/' + camera_id + '.jpg',
                'wb') as f:
            # for chunk in content.iter_content(chunk_size=1024):
            #     if chunk:
            f.write(content)
        if camera_rec:
            _t_cc_name = "(%s)" % (camera_rec.cam_name) if camera_rec.cam_name else ''
            camera = {
                'id': camera_rec.id,
                'name': "%s %s" % (camera_rec.name, _t_cc_name),
                'camera_url': request.httprequest.host_url + 'ars_auto_lpr/static/src/bay_images/' + camera_id + '.jpg',
                            # '?rand=' + str(random.randint(0, 1000)),
                'bays': {},
            }
            for bay in camera_rec.alpr_bay_ids:
                _b_data = bay.read(API_FIELDS['bay'])[0]
                _b_data['bay_id'] = bay.bay_id.id
                if 'id' in _b_data:
                    del _b_data['id']
                camera['bays'][bay.bay_id.id] = _b_data
        return camera

    @http.route('/ars_auto_lpr/get_camara_information', type='json', auth='public', cors='*')
    def alpr_get_camera_information(self, camera_id=None, **kw):
        _logger.info("Executing alpr_get_camera_information...")
        db, user, password = request.get_json_data().get('db', False), request.get_json_data().get('user',
                                                                                           False), request.get_json_data().get(
            'password', False)
        if db and user and password:
            uid = request.session.authenticate(db, {'login': user, 'password': password, 'type': 'password'})
            if uid:
                cameras = []
                request_type = []
                request_type += [{
                    'req_type': request.env.company.evaluation_type,
                    'token': request.env.company.token,
                    'dealer_code':request.env.company.dealer_code,
                }]
                camera_recs = request.env['ac.ars.ip.camera'].search([('hik_vision', '=', True)])
                _logger.info("Fetching Camera Details")
                for camera_rec in camera_recs:
                    _bays = []
                    _t_cc_name = "(%s)" % (camera_rec.cam_name) if camera_rec.cam_name else ''
                    for bay in camera_rec.alpr_bay_ids:
                        bay_log = request.env['alpr.bay.vehicle.log'].search(
                            [('bay_id', '=', bay.bay_id.id), ('camera_id', '=', camera_rec.id)], order='id desc',
                            limit=1)
                        vehicle_number = bay_log.vehicle_number
                        _logger.info(bay.bay_id.name, vehicle_number, "Entry type", bay_log.entry_type)
                        _bays += [{
                            'bay_id': bay.bay_id.id,
                            'bay_name': bay.bay_id.name,
                            'is_bay_occupy': bay.is_bay_occupy,
                            'x1': bay.disp_rel_area_x,
                            'y1': bay.disp_rel_area_y,
                            'x2': bay.disp_rel_area_x + bay.disp_rel_area_w,
                            'y2': bay.disp_rel_area_y + bay.disp_rel_area_h,
                            'vehicle_number': vehicle_number,
                        }]
                    cameras += [{
                        'camera_id': camera_rec.id,
                        'camera_ip': camera_rec.name,
                        'camera_name': camera_rec.cam_name,
                        'camera_url': camera_rec.alpr_camera_url,
                        'port_num': camera_rec.http_port,
                        'bays': _bays,
                        'username': camera_rec.user_name,
                        'password': camera_rec.password,
                        'req_type': request_type,
                    }]
                response = {'cameras': cameras}
            else:
                response = "Authentication Problem"
            return json.dumps(response)

    @http.route('/ars_auto_lpr/process_numplate_info', type='json', auth='public', cors='*')
    def alpr_process_numplate_information(self, **kw):
        _logger.info("Executing alpr_process_numplate_information...")
        db, user, password = request.get_json_data().get('db', False), request.get_json_data().get('user',
                                                                                           False), request.get_json_data().get(
            'password', False)
        response = "Connected"
        if db and user and password:
            uid = request.session.authenticate(db, {'login': user, 'password': password, 'type': 'password'})
            if uid:
                current_date = str(datetime.now().date())
                response = {
                    'status': False,
                    'title': 'Oops! Something went wrong',
                    'message': 'We are unable to process this request. Please try again later.',
                }
                vehicle_number = kw['plate']
                camera_id = kw['cam_id']
                bay_id = kw['bay_id']
                entry_type = kw['type']
                log_recs = request.env['alpr.bay.vehicle.log'].search([('bay_id', '=', bay_id)], order='id desc',
                                                                      limit=1)
                cr = request.env.cr
                cr.execute("""select count(distinct bl.vehicle_number) as count_value, rc.id from alpr_bay_vehicle_log bl INNER JOIN resource_resource rr on bl.bay_id = rr.id 
                                            INNER JOIN resource_category rc on rr.resource_category = rc.id  where log_date ='""" + str(
                    current_date) + """'group by rc.id""")
                dashbord_data = cr.dictfetchall()
                for data in dashbord_data:
                    res_cat = request.env['resource.category'].search([('id', '=', data.get('id'))])
                    res_cat.write(data)
                pattern = "^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$"
                patten2 = "^[A-Z]{2}[0-9][A-Z][A-Z]{2}[0-9]{4}$"

                if len(log_recs) > 0 and (re.match(pattern, vehicle_number) or re.match(patten2, vehicle_number)):
                    if log_recs[0].vehicle_number[-4:] == vehicle_number[-4:]:
                        if log_recs[0].entry_type == 'out':
                            _logger.info("------|||Vehicle Got Deleted|||------", log_recs[0].vehicle_number)
                            log_recs[0].unlink()
                            alpr_bay = request.env['alpr.camera.bay'].search(
                                [('bay_id', '=', bay_id), ('camera_id', '=', camera_id)])
                            alpr_bay.write({'is_bay_occupy': True, 'count_log': 0})
                        elif log_recs[0].entry_type != 'out':
                            _logger.info("------|||Vehicle In BAY|||------", log_recs[0].vehicle_number)
                            alpr_bay = request.env['alpr.camera.bay'].search(
                                [('bay_id', '=', bay_id), ('camera_id', '=', camera_id)])
                            alpr_bay.write({'is_bay_occupy': True, 'count_log': 0})
                        return response
                    else:
                        bay_log = request.env['alpr.bay.vehicle.log'].search(
                            [('vehicle_number', '=', vehicle_number)], order='id desc', limit=1)
                        if bay_log and bay_log.entry_type != 'out':
                            _logger.info("<<<<<<<<<< Out Entry Creating >>>>>>>>>>>")
                            request.env['alpr.bay.vehicle.log'].create({
                                'vehicle_number': bay_log.vehicle_number,
                                'camera_id': camera_id,
                                'bay_id': bay_log.bay_id.id,
                                'entry_type': 'out',
                                'log_date': current_date,
                                'out_datetime': fields.Datetime.from_string(fields.Datetime.now())
                            })
                        alpr_bay = request.env['alpr.camera.bay'].search(
                            [('bay_id', '=', bay_id), ('camera_id', '=', camera_id)])
                        alpr_bay.write({'is_bay_occupy': True, 'count_log': 0})
                        # if bay_log and bay_log.vehicle_number != "XXXX":
                        _logger.info("New Entry Created >>>>>>>>>>>>>")
                        request.env['alpr.bay.vehicle.log'].create({
                            'vehicle_number': vehicle_number,
                            'camera_id': camera_id,
                            'bay_id': bay_id,
                            'entry_type': 'in',
                            'log_date': current_date
                        })
                else:
                    vals = {
                        'vehicle_number': vehicle_number,
                        'camera_id': camera_id,
                        'bay_id': bay_id,
                        'entry_type': entry_type,
                        'log_date': current_date
                    }
                    _logger.info(vals)
                    # request.env['alpr.bay.vehicle.log'].create()
        return response

    @http.route('/ars_auto_lpr/set_camera_data', type='json', auth='user')
    def alpr_set_camera_data(self, camera_id=None, areas=None):
        _logger.info("Executing alpr_set_camera_data...")
        response = {
            'status': False,
            'title': 'Oops! Something went wrong',
            'message': 'We are unable to process this request. Please try again later.',
        }
        camera_rec = request.env['ac.ars.ip.camera'].search([('id', '=', int(camera_id))])
        if not camera_rec:
            response['title'] = 'Error'
            response['message'] = 'You have selected an invalid camera.'
            return response

        status = camera_rec.save_bay_areas(areas)
        if status:
            response['status'] = True
            response['title'] = 'Saved'
            response['message'] = 'Bay details saved successfully.'
            # response['data'] = self.alpr_get_camera_data(camera_id=camera_id)

        return response

    @http.route('/ars_auto_lpr/api/cameras', type='http', auth='user', cors='*')
    def alpr_get_cameras(self, **kw):
        _logger.info("Executing alpr_get_cameras...")
        cameras = []
        camera_ids = request.env['alpr.camera'].search([('id', '>', 0)])
        for camera in camera_ids:
            _bays = []
            for bay in camera.alpr_bay_ids:
                _bays += [{
                    'bay_id': bay.bay_id.id,
                    'bay_name': bay.bay_id.name,
                    'x1': bay.disp_rel_area_x,
                    'y1': bay.disp_rel_area_y,
                    'x2': bay.disp_rel_area_w,
                    'y2': bay.disp_rel_area_h,
                }]
            cameras += [{
                'camera_id': camera.id,
                'camera_ip': camera.name,
                'camera_name': camera.camera_name,
                'camera_url': camera.alpr_camera_url,
                'port_num': camera.port_num,
                'update_interval': camera.update_interval,
                'bays': _bays,
            }]

        response = {'cameras': cameras}
        return self.alpr_api_response(response, kw)

    @http.route('/ars_auto_lpr/api/log_bay_vehicle_number', type='http', auth='user', cors='*')
    def alpr_log_bay_vehicle(self, **kw):
        _logger.info("Executing alpr_log_bay_vehicle...")
        response = {
            'status': False,
            'title': 'Oops! Something went wrong',
            'message': 'We are unable to process this request. Please try again later.',
        }

        vehicle_number = kw.get('vehicle_number', '')
        if vehicle_number != '':
            vehicle_number = vehicle_number.strip()

        if not vehicle_number:
            response['title'] = 'Validation Error'
            response['message'] = 'Vehicle_Number is required.'
            return self.alpr_api_response(response, kw)

        camera_id = kw.get('camera_id', '')
        if camera_id != '':
            camera_id = camera_id.strip()
        if not camera_id:
            response['title'] = 'Validation Error'
            response['message'] = 'Camera_Id is required.'
            return self.alpr_api_response(response, kw)
        else:
            camera_id = int(camera_id)
            camera_count = request.env['alpr.camera'].search_count([('id', '=', camera_id)])
            if camera_count == 0:
                response['title'] = 'Validation Error'
                response['message'] = 'Invalid value for Camera_Id.'
                return self.alpr_api_response(response, kw)

        bay_id = kw.get('bay_id', '')
        if bay_id != '':
            bay_id = bay_id.strip()
        if not bay_id:
            response['title'] = 'Validation Error'
            response['message'] = 'Bay_Id is required.'
            return self.alpr_api_response(response, kw)
        else:
            bay_id = int(bay_id)
            bay_count = request.env['resource.resource'].search_count([('id', '=', bay_id), ('resource_category.alpr_is_bay', '=', True)])
            if bay_count == 0:
                response['title'] = 'Validation Error'
                response['message'] = 'Invalid value for Bay_Id.'
                return self.alpr_api_response(response, kw)     

        try:
            request.env['alpr.bay.vehicle.log'].create({
                'vehicle_number': vehicle_number,
                'camera_id': camera_id,
                'bay_id': bay_id,
            })
            response['status'] = True
            response['title'] = 'Success'
            response['message'] = 'Log created successfully.'
        except:
            response['title'] = 'Database Error'
            response['message'] = 'Failed to log vehicle number.'

        return self.alpr_api_response(response, kw)


    def alpr_api_response(self, response, kw):
        _logger.info("Executing alpr_api_response...")
        response = json.dumps(response)
        if 'callback' in kw:
            return kw['callback']+'('+ response +')'
        return response

    @http.route('/ars_auto_lpr/alpr_bay_status', type='json', auth='public', cors='*')
    def alpr_bay_status(self, **kw):
        _logger.info("Executing alpr_bay_status...")
        db, user, password = request.get_json_data().get('db', False), request.get_json_data().get('user',
                                                                                           False), request.get_json_data().get(
            'password', False)
        if db and user and password:
            uid = request.session.authenticate(db, {'login': user, 'password': password, 'type': 'password'})
            if uid:
                current_date = str(datetime.now().date())
                bay_id, camera_id = request.get_json_data().get('bay_id'), request.get_json_data().get('cam_id')
                alpr_bay = request.env['alpr.camera.bay'].search(
                    [('bay_id', '=', bay_id), ('camera_id', '=', camera_id)])
                if alpr_bay.count_log == 5:
                    bay_log = request.env['alpr.bay.vehicle.log'].search(
                        [('bay_id', '=', bay_id), ('camera_id', '=', camera_id)], order='id desc', limit=1)
                    bay_log.write({'out_datetime': fields.Datetime.from_string(fields.Datetime.now())})
                    alpr_bay.write({'is_bay_occupy': False, 'count_log': 0})
                    _logger.info(alpr_bay.bay_id.name, bay_log.vehicle_number, "Out")
                    request.env['alpr.bay.vehicle.log'].create({
                        'vehicle_number': bay_log.vehicle_number,
                        'camera_id': camera_id,
                        'bay_id': bay_id,
                        'entry_type': 'out',
                        'log_date': current_date,
                        'out_datetime': fields.Datetime.from_string(fields.Datetime.now())
                    })
                elif alpr_bay.is_bay_occupy:
                    count = int(alpr_bay.count_log) + 1
                    _logger.info("alpr_bay.count_log >>>> ", alpr_bay.count_log)
                    alpr_bay.write({'count_log': count})

    @http.route('/ars_auto_lpr/online/server', type='json', auth='public', cors='*')
    def alpr_online_server(self, **kw):
        _logger.info("Executing alpr_online_server...")
        db, user, password = request.get_json_data().get('db', False), request.get_json_data().get('user',
                                                                                           False), request.get_json_data().get(
            'password', False)
        if db and user and password:
            uid = request.session.authenticate(db, {'login': user, 'password': password, 'type': 'password'})
            if uid:
                online_server = request.env['alpr.server.online']
                cam_obj, encoded_string = request.get_json_data().get('cam_obj', False), request.get_json_data().get(
                    'encoded_string', False)
                # threading.Thread(target=online_server.validate_and_create_log, args=(cam_obj,encoded_string)).start()
                responce = online_server.validate_and_create_log(cam_obj, encoded_string)
            return responce



