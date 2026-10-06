# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AcArsVideoPlayback(models.TransientModel):
    _name = "ac.ars.video.playback"
    _description = 'Video Playback Wizard'
    
    name = fields.Char()
    html = fields.Html()
    
    @api.onchange('name')
    def get_html(self):
        _logger.info("Executing get_html...")
        html = ''
        html += '<video width="400" controls>'
        html += '<source src="/static/src/video/Video.mp4" type="video/mp4">'
        html += '</video>'
        html += '<h1>Amal Mohan<h1>'
        self.html = html
