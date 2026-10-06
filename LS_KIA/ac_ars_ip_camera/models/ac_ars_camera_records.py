# -*- coding: utf-8 -*-
import cv2
import requests
import logging
from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class AcArsCameraRecords(models.Model):
    _name = 'ac.ars.camera.records'
    _inherit = 'mail.thread'
    _description = 'ARS Camera Records'
    _rec_name = 'camera_id'

    camera_id = fields.Many2one('ac.ars.ip.camera', 'Camera')
    cam_name = fields.Char(related='camera_id.cam_name', string='Camera Name')
    cam_brand = fields.Many2one('ac.ars.camera.config', related='camera_id.cam_brand', string="Brand")
    company_id = fields.Many2one('res.company', "Company")
    
    status = fields.Selection([
        ('not_recording', 'New Records'), 
        ('recording', 'Recording'), 
        ('processing', 'Processing'),
        ('recorded', 'Recorded'), 
        ('exception', 'Exception')
    ], default='not_recording', string="Status")
    
    cam_status = fields.Selection([
        ('online', 'Online'), 
        ('offline', 'Offline'),
        ('unknown', 'Unknown'), 
        ('progress', 'In Progress')
    ], default='unknown', string="Camera Status")
    
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    duration = fields.Char(compute='_compute_time', string="Duration")
    cam_pid = fields.Char(string="PID")
    error_exception = fields.Text("Exception")

    @api.depends('start_date', 'end_date')
    def _compute_time(self):
        _logger.info("Executing _compute_time...")
        for case in self:
            if case.start_date and case.end_date:
                start_time = case.start_date
                end_time = case.end_date
                stream_duration = end_time - start_time
                case.duration = str(stream_duration) + " min"
            else:
                case.duration = "0 min"

    def start_recording(self):
        _logger.info("Executing start_recording...")
        ip_cam = self.env['ac.ars.ip.camera'].browse(self.camera_id.id)
        if ip_cam.status == 'online':
            self.status = 'recording'
            self.start_date = fields.Datetime.now()
            return True
        return False

    def start_call_ffmpeg_server(self):
        _logger.info("Executing start_call_ffmpeg_server...")
        # We handle this via requests in modern Odoo. 
        # In a fully modular ecosystem, resource.name logic might need an interface.
        URL = f"http://{self.camera_id.server_location}/start?ip={self.camera_id.name}&port={self.camera_id.http_port}&uname={self.camera_id.user_name}&pwd={self.camera_id.password}&path={self.camera_id.dir_name}&name={self.camera_id.record_stream_file}"
        try:
            if self.camera_id.get_rtsp_url() and self.camera_id.rtsp_status == 'online':
                response = requests.get(url=URL, params={'RTSP_URL': self.camera_id.get_rtsp_url()})
                cam_response = response.text
                self.write({'cam_pid': str(int(cam_response) + 1)})
            else:
                self.write({'cam_pid': 'NOT FOUND', 'error_exception': 'Unknown rtsp URL'})
            return True
        except Exception as e:
            self.write({'status': 'exception', 'cam_pid': 'NOT FOUND', 'error_exception': str(e)})
            return False

    def stop_call_ffmpeg_server(self):
        _logger.info("Executing stop_call_ffmpeg_server...")
        if self.cam_pid != 'NOT FOUND' and self.status == 'recording':
            try:
                self.status = 'processing'
                url = f"http://{self.camera_id.server_location}/stop?pid={self.cam_pid}"
                response = requests.get(url)
                if response.status_code == 200:
                    self.stop_recording()
                return True
            except Exception as e:
                self.write({'error_exception': str(e)})
                return False
        else:
            return False

    def stop_recording(self):
        _logger.info("Executing stop_recording...")
        self.status = 'recorded'
        self.end_date = fields.Datetime.now()
        return True
