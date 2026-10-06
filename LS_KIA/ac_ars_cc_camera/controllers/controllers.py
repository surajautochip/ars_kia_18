# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _
import datetime
import logging

_logger = logging.getLogger(__name__)

class LiveStreamToken(http.Controller):

    @http.route('/live_stream/generate/link', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def live_stream_generate_link_controller(self, token, **kw):
        _logger.info("Executing live_stream_generate_link_controller...")
        token_obj = request.env['ac.ars.live.stream.token'].search([('id', '=', token)])
        res = {'result': token_obj.generate_live_stream_link()}
        return res

    @http.route('/customer/sms/send', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def live_stream_sms_send_controller(self, token, **kw):
        _logger.info("Executing live_stream_sms_send_controller...")
        token_obj = request.env['ac.ars.live.stream.token'].search([('id', '=', token)])
        res = {'result': token_obj.ac_ars_live_streaming_send_sms()}
        return res

    @http.route('/customer/email/send', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def live_stream_email_send_controller(self, token, **kw):
        _logger.info("Executing live_stream_email_send_controller...")
        token_obj = request.env['ac.ars.live.stream.token'].search([('id', '=', token)])
        res = {'result': token_obj.ac_ars_live_streaming_send_mail()}
        return res

    @http.route('/live_stream/camera/start', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def live_stream_camera_start_controller(self, token, **kw):
        _logger.info("Executing live_stream_camera_start_controller...")
        token_obj = request.env['ac.ars.live.stream.token'].search([('id', '=', token)])
        res = token_obj.ac_ars_live_streaming_camera_start()
        return res
