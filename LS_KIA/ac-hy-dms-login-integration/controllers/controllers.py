# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)

class DMS_Connector(http.Controller):
    @http.route('/dms/link/update', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def ls_dms_link_update(self, token, **kw):
        _logger.info("Executing ls_dms_link_update...")
        token_obj = request.env['ac.ars.live.stream.token'].search([('id', '=', token)])
        res = {'result': token_obj.send_live_stream_link()}
        return res

#     @http.route('/ac-hy-dms-login-integration/ac-hy-dms-login-integration/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac-hy-dms-login-integration.listing', {
#             'root': '/ac-hy-dms-login-integration/ac-hy-dms-login-integration',
#             'objects': http.request.env['ac-hy-dms-login-integration.ac-hy-dms-login-integration'].search([]),
#         })

#     @http.route('/ac-hy-dms-login-integration/ac-hy-dms-login-integration/objects/<model("ac-hy-dms-login-integration.ac-hy-dms-login-integration"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac-hy-dms-login-integration.object', {
#             'object': obj
#         })
