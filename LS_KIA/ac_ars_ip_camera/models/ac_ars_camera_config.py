# -*- coding: utf-8 -*-
from odoo import models, fields

class AcArsCameraConfig(models.Model):
    _name = 'ac.ars.camera.config'
    _description = 'ARS Camera Configuration'

    name = fields.Char(string='Brand Name')
    rtsp_url = fields.Text(string='RTSP URL Template')
