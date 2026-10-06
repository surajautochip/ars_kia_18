import logging
_logger = logging.getLogger(__name__)

import io
import base64
import pytz
import urllib.parse
import threading
import requests
from datetime import datetime, timedelta
from odoo import models, fields, api, http
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import json


class AcArsLiveStreamToken(models.Model):
    _name = 'ac.ars.live.stream.token'
    _description = "Live Stream Token"
    _rec_name = "token"
    _order = "date"

    active = fields.Boolean('Active', default=True)
    state = fields.Selection([('draft', 'Draft'), ('valid', 'Valid'), ('invalid', 'Invalid')])
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', 'Company')
    user_id = fields.Many2one('res.users', 'User')
    plan_event_id = fields.Many2one('calendar.event', 'Plan Event')
    event_id = fields.Many2one('calendar.event', 'Actual Event')
    project_task_ids = fields.Many2many('project.task')
    sale_order_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner')
    email_id = fields.Many2one('mail.mail')
    dms_ro_number = fields.Many2one('ac.ars.allocation.data', 'RO Number')
    email_state = fields.Selection([('outgoing', 'Outgoing'), ('sent', 'Sent'), ('received', 'Received'),
                                    ('exception', 'Delivery Failed'), ('cancel', 'Cancelled')], related="email_id.state"
                                   )
    sms_id = fields.Many2one('ac.ars.sms.record')
    sms_stage = fields.Selection([('outgoing', 'Outgoing'), ('sent', 'Sent'), ('received', 'Received'),
                                  ('exception', 'Delivery Failed'), ('cancel', 'Cancelled'),
                                  ('not_found', 'Not Found')], related="sms_id.stage")
    resource = fields.Many2one('resource.resource')
    camera_rec_ids = fields.Many2many('ac.ars.camera.records')
    status = fields.Selection([('live', 'Live'), ('completed', 'Completed'), ('hold', 'Hold')])
    token = fields.Char()
    url = fields.Text()
    reason_selection = fields.Selection([('waiting for approval', 'Waiting For Customer Approval'),
                                         ('waiting for parts', 'Waiting For Parts'),
                                         ('waiting for diagnosis', 'Waiting For Diagnosis'),
                                         ('waiting for decision', 'Waiting for Decision'),
                                         ('other', 'Other')], string='Reason')

    other_reason = fields.Text('Remark')

    def finish_live_stream(self):
        _logger.info("Executing finish_live_stream...")
        try:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            c = fields.Datetime.now()
            today = (c.replace(tzinfo=pytz.utc).astimezone(user_tz)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            if self.plan_event_id:
                self.plan_event_id.write({'stop_datetime': self.plan_event_id.stop})
            if self.event_id:
                self.event_id.write({'stop_datetime': today})
            res = self.env['calendar.event'].close_ccip(self.token)
            
            try:
                self.ac_ars_live_streaming_camera_stop()
            except Exception as cam_e:
                _logger.warning("Camera stop skipped or failed: %s", cam_e)
                
            try:
                self.project_task_ids.write({'stage_id': 39})
            except Exception as task_e:
                _logger.warning("Failed to update project task stage: %s", task_e)
            self.state = 'invalid'
            self.status = 'completed'
            self.active = False
            
            if self.dms_ro_number and self.dms_ro_number.state != 'done':
                self.dms_ro_number.write({'state': 'done'})
                self.env['bus.bus']._sendone('ac_ars_live_stream_channel', 'stream_updated', {'id': self.dms_ro_number.id})
            
            # Create a record in Total Data (ac.ars.live.streaming)
            try:
                # Calculate a start time (fallback to token's create_date or today)
                start_dt = self.create_date if self.create_date else fields.Datetime.now()
                end_dt = fields.Datetime.now()
                
                # Try to find existing Total Data record to prevent duplicates
                total_data = self.env['ac.ars.live.streaming'].search([('name', '=', self.token)], limit=1)
                if not total_data:
                    self.env['ac.ars.live.streaming'].create({
                        'name': self.token or f"TOKEN-{self.id}",
                        'date': start_dt,
                        'stream_start_time': start_dt,
                        'stream_end_time': end_dt,
                        'cust_name': self.partner_id.name if self.partner_id else (self.dms_ro_number.partner_id.name if self.dms_ro_number else ''),
                        'vehicle_no': self.dms_ro_number.dms_ro_no if self.dms_ro_number else (self.plan_event_id.name if self.plan_event_id else ''),
                        'dms_ro_number': self.dms_ro_number.id if self.dms_ro_number else False,
                        'company_id': self.company_id.id or self.env.company.id,
                        'state': 'finished'
                    })
            except Exception as inner_e:
                _logger.error("Failed to create Total Data record: %s", inner_e)

            return True
        except Exception as e:
            _logger.error("Error while stopping the live stream: %s", e)
            return False

    def call_finish_live_stream(self):
        _logger.info("Executing call_finish_live_stream...")
        for token in self.env['ac.ars.live.stream.token'].search([('state', '=', 'valid')]):
            token.finish_live_stream()
        return {}

    def cron_finish_live_stream(self):
        _logger.info("Executing cron_finish_live_stream...")
        self.call_finish_live_stream()

    def generate_live_stream_link(self):
        _logger.info("Executing generate_live_stream_link...")
        res = self.event_id.push_ccip(self.resource)
        if res and res.get('token') and res.get("url"):
            url_decode = urllib.parse.unquote(res.get("url"))
            self.write({'token': res.get('token'), 'url': url_decode})
            return True
        else:
            return False

    def ac_ars_live_streaming_send_mail(self):
        _logger.info("Executing ac_ars_live_streaming_send_mail...")
        template = self.env.ref('ac_ars_cc_camera.mail_template_ac_ars_live_streaming__notification')
        email = template.send_mail(self.id, email_values={'email_to': self.partner_id.email}, force_send=True)
        self.email_id = int(email)
        return True

    def ac_ars_live_streaming_send_sms(self):
        _logger.info("Executing ac_ars_live_streaming_send_sms...")
        now = datetime.now()
        sms_values = {'name': self.partner_id.name, 'phone': self.partner_id.phone, 'regno': self.plan_event_id.name,
                      'company_id': self.company_id.id, 'date': now, 'url': self.url}
        create_and_send_sms = self.env['ac.ars.sms.record'].create(sms_values)
        res = create_and_send_sms.sent_an_sms()
        self.sms_id = create_and_send_sms.id
        
        # 2. Execute WhatsApp
        try:
            _logger.info("Checking WhatsApp configuration...")
            whatsapp_config = self.env['ac.ars.whatsapp.config'].sudo().search([('company_id', '=', self.company_id.id)], limit=1)
            if not whatsapp_config:
                whatsapp_config = self.env['ac.ars.whatsapp.config'].sudo().search([], limit=1)
                
            if whatsapp_config:
                _logger.info("Calling send_whatsapp()...")
                whatsapp_config.send_whatsapp(self.partner_id.name, self.partner_id.phone, self.plan_event_id.name, self.url)
                _logger.info("Successfully executed send_whatsapp to %s", self.partner_id.phone)
            else:
                _logger.warning("No WhatsApp configuration found for company.")
        except Exception as e:
            _logger.error("Exception when executing WhatsApp: %s", str(e))
            
        return res

    def ac_ars_live_streaming_camera_start(self):
        _logger.info("Executing ac_ars_live_streaming_camera_start...")
        global camera_record
        res, cameras = {}, []
        if self.camera_rec_ids and self.status != 'hold':
            for cam in self.camera_rec_ids:
                if cam.status == 'exception':
                    cameras.extend(cam.camera_id)
            if not cameras:
                res.update({'status': True,
                            'message': 'Cameras are started'})
                return res
        self.status = 'live'
        for cam in cameras if cameras != [] else self.resource.ip_address:
            URL = f"http://{cam.server_location}/start?ip={cam.name}&port={cam.http_port}&uname={cam.user_name}&pwd={cam.password}&path={cam.dir_name}&BAY={self.resource.name}&name={cam.record_stream_file}"
            camera_data = {'company_id': self.company_id.id, 'camera_id': cam.id,
                           'cam_status': cam.rtsp_status,
                           'status': 'recording',
                           }
            ac_ars_camera_details = {}
            camera_record = False
            try:
                camera_record = self.env['ac.ars.camera.records'].create(camera_data)
                if cam.get_rtsp_url():
                    response = requests.get(url=URL, params={'RTSP_URL': cam.get_rtsp_url(),
                                                             'cam_url': camera_record.id,
                                                             'recording': cam.recording,
                                                             'reels_time': cam.reel_time})
                    cam_response = response.text
                    ac_ars_camera_details.update({'cam_pid': int(cam_response) + 1})
                    res.update({'status': True})
                else:
                    ac_ars_camera_details.update({'status': 'exception',
                                           'cam_pid': 'NOT FOUND',
                                           'cam_status': cam.rtsp_status,
                                           'error_exception': 'Camera not reachable or Wrong URL'})
                    if 'status' in res and res['status']:
                        res.update({'status': False,
                                    'message': 'One camera could not able to access! Do you want to retry?'})
                    else:
                        res.update({'status': False,
                                    'message': 'Camera could not able to access! Do you want to retry?'})
            except Exception as e:
                camera_data.update({'status': 'exception', 'cam_pid': 'NOT FOUND', 'error_exception': e})
                if not camera_record:
                    camera_record = self.env['ac.ars.camera.records'].create(camera_data)
                self.write({'camera_rec_ids': [(4, camera_record.id)]})
                return {'status': False, 'cam_pid': 'NOT FOUND', 'error_exception': e,
                        'message': 'Could not able to access the Camera server! Do you want to retry?'}
            camera_record.write(ac_ars_camera_details)
            self.write({'camera_rec_ids': [(4, camera_record.id)]})
            camera_record.start_recording()
        return res

    def ac_ars_live_streaming_camera_stop(self):
        _logger.info("Executing ac_ars_live_streaming_camera_stop...")
        result = {}
        for cam_rec in self.camera_rec_ids:
            _logger.info("Evaluating cam_rec %s: cam_pid=%s, status=%s", cam_rec.id, cam_rec.cam_pid, cam_rec.status)
            if cam_rec.cam_pid != 'NOT FOUND' and cam_rec.status == 'recording':
                try:
                    params = {'cam_url': cam_rec.id, 'recording': cam_rec.camera_id.recording,
                              'reels_time': cam_rec.camera_id.reel_time}
                    cam_rec.status = 'processing'
                    if cam_rec.cam_pid != 'NOT FOUND':
                        url = f"http://{cam_rec.camera_id.server_location}/stop?pid={cam_rec.cam_pid}"
                        _logger.info("Stopping camera via URL: %s", url)
                        response = requests.get(url=url, params=params)
                        _logger.info("Stop response: %s", response.status_code)
                        if response.status_code == 200:
                            cam_rec.stop_recording()
                        result.update({'response': response, 'status': response.status_code})
                    else:
                        result.update({'response': 'NOT FOUND', 'status': 404})
                except Exception as e:
                    _logger.error("Exception stopping camera: %s", e)
                    cam_rec.write({'error_exception': e})
                    result.update({'response': e, 'status': 500})
            else:
                _logger.warning("Condition not met to stop camera %s. Setting exception.", cam_rec.id)
                cam_rec.write({'status': 'exception'})
                result.update({'response': 'NOT FOUND', 'status': 404})
        return result

    def calendar_event_resume(self):
        _logger.info("Executing calendar_event_resume...")
        resource = self.resource
        for task in self.project_task_ids:
            tech_entrys = task.timesheet_ids.filtered(
                lambda x: x.entry_type == 'actual' and x.resource_name == resource and x.is_release == False)
            if tech_entrys:
                tech_entry = tech_entrys[-1]
                self.timesheet_create_resource_wise(tech_entry, task, 'Tech')
                bay_entry = task.timesheet_ids.filtered(lambda
                                                            x: x.entry_type == 'actual' and x.resource_name == tech_entry.mapped_bay_resource and not x.end_datetime)
                if not bay_entry:
                    self.timesheet_create_resource_wise(tech_entry, task, 'Bay')
            task.stage_id = self.env['project.task.type'].search([('sequence', '=', 1)]).id
            self.sale_order_id.write({'main_process_id': (self.env.ref("ac_rms.main_process10", raise_if_not_found=False).id if self.env.ref("ac_rms.main_process10", raise_if_not_found=False) else False)})
            return {}

    def ac_ars_live_streaming_resume(self):
        _logger.info("Executing ac_ars_live_streaming_resume...")
        self.status = 'live'
        self.ac_ars_live_streaming_camera_start()
        self.calendar_event_resume()
        return True

    def ac_ars_live_streaming_pause(self, reason=None, remark=None):
        _logger.info("Executing ac_ars_live_streaming_pause...")
        if self.state == 'valid' and self.status == 'live':
            self.status = 'hold'
            self.reason_selection = reason
            self.other_reason = remark
            self.ac_ars_live_streaming_camera_stop()
            self.calendar_event_pause()
        return True

    def calendar_event_pause(self):
        _logger.info("Executing calendar_event_pause...")
        for task in self.project_task_ids:
            task.sudo().timesheet_ids.filtered(lambda x: hasattr(x, 'entry_type') and getattr(x, 'entry_type') == 'actual' and hasattr(x, 'end_datetime') and not getattr(x, 'end_datetime')).write(
                {'end_datetime': fields.Datetime.now()})
            
            resource = self.resource
            resource_type_id = False
            if hasattr(resource, 'resource_category') and getattr(resource, 'resource_category'):
                resource_type_id = resource.resource_category.id
                
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            status2 = self.env.ref("ac_rms.status2", raise_if_not_found=False)
            
            timesheet_data_entry = {
                'account_id': 1,
                'date': fields.Datetime.now(),
                'status': status2.id if status2 else False,
                'entry_type': 'actual',
                'resource_type': resource_type_id,
                'resource_name': resource.id if hasattr(resource, 'id') else False,
                'start_datetime': fields.Datetime.now(),
                'end_datetime': False,
                'break_reason': self.reason_selection if getattr(self, 'reason_selection', '') != 'others' else getattr(self, 'other_reason', ''),
                'employee_id': employee.id if employee else False,
                'name': task.name
            }
            task.sudo().timesheet_ids = [(0, 0, timesheet_data_entry)]
            stage = self.env.ref("ac_rms.rms_stage3", raise_if_not_found=False)
            if stage:
                task.stage_id = stage.id
        
        main_process = self.env.ref("ac_rms.main_process11", raise_if_not_found=False)
        if main_process:
            self.sale_order_id.write({'main_process_id': main_process.id})
            
        current_time = fields.Datetime.now()
        
        if self.event_id:
            self.event_id.write({
                'stop': current_time,
                'stop_date': fields.Date.today(),
                'stop_datetime': current_time
            })

    def timesheet_create_resource_wise(self, resource, task, category):
        _logger.info("Executing timesheet_create_resource_wise...")
        uid = self.user_id.id if self.user_id else self.env.user.id
        employee = self.env['hr.employee'].search([('user_id', '=', uid)], limit=1)
        
        status1 = self.env.ref("ac_rms.status1", raise_if_not_found=False)
        
        resource_type_id = False
        resource_name_id = False
        
        if category == 'Tech' and hasattr(resource, 'resource_name') and resource.resource_name:
            if hasattr(resource.resource_name, 'resource_category') and resource.resource_name.resource_category:
                resource_type_id = resource.resource_name.resource_category.id
            resource_name_id = resource.resource_name.id
        elif category == 'Bay' and hasattr(resource, 'mapped_bay_resource') and resource.mapped_bay_resource:
            if hasattr(resource.mapped_bay_resource, 'resource_category') and resource.mapped_bay_resource.resource_category:
                resource_type_id = resource.mapped_bay_resource.resource_category.id
            resource_name_id = resource.mapped_bay_resource.id
            
        timesheet_data_entry = {
            'account_id': 1,
            'date': fields.Datetime.now(),
            'status': status1.id if status1 else False,
            'entry_type': 'actual',
            'resource_type': resource_type_id,
            'resource_name': resource_name_id,
            'start_datetime': fields.Datetime.now(),
            'end_datetime': False,
            'break_reason': False,
            'employee_id': employee.id if employee else False,
            'name': task.name
        }
        task.sudo().timesheet_ids = [(0, 0, timesheet_data_entry)]
        return {}


class AcArsPlannerCalendarEvent(models.Model):
    _inherit = 'calendar.event'
    ac_ars_live_stream_token_id = fields.Many2one('ac.ars.live.stream.token')

    def create_token(self, res):
        _logger.info("Executing create_token...")
        token_obj = self.env['ac.ars.live.stream.token'].create(res)
        return token_obj

    def push_ccip(self, bay_obj):
        res = {}
        querystring = {}
        cr = self._cr
        company = self.env.company
        val = 0
        querystring['company_name'] = str(company.name)
        querystring['bay_name'] = bay_obj.name
        for ip in bay_obj.ip_address:
            val = val + 1
            querystring['username' + str(val)] = ip.user_name
            querystring['password' + str(val)] = ip.password
            querystring['ip' + str(val)] = ip.name
        try:
            url = "http://localhost:4500/index.php/geturl"
            response = requests.request("POST", url, params=querystring)
            _logger.info('Response from PHP server %s', response.text)
            if response.text:
                response = json.loads(response.text)
                if response.get('status'):
                    _logger.info('Token Generated and updated.')
                    res.update({'token': response.get('token'), 'url': response.get('url')})
                    return res
            else:
                return res
        except Exception as e:
            _logger.error('Error while generate token!!!!!!!!!! %s', e)
            return res

    def close_ccip(self, event_token):
        res = {}
        token = event_token
        try:
            url = "http://localhost:4500/index.php/stop?token=" + str(token)
            response = requests.request("GET", url, params={'token': token})
            _logger.error('RESPONSE.........: %s', response.text)
            if response.text:
                response = json.loads(response.text)
                res.update({'response': response})
            return res
        except Exception as e:
            _logger.error('Error while generate token!!!!!!!!!! %s', e)
            return res
