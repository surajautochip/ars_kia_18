# -*- coding: utf-8 -*-
from odoo import http

# class HyWhatsappApi(http.Controller):
#     @http.route('/ac_ars_hy_whatsapp_api/ac_ars_hy_whatsapp_api/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ac_ars_hy_whatsapp_api/ac_ars_hy_whatsapp_api/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ac_ars_hy_whatsapp_api.listing', {
#             'root': '/ac_ars_hy_whatsapp_api/ac_ars_hy_whatsapp_api',
#             'objects': http.request.env['ac_ars_hy_whatsapp_api.ac_ars_hy_whatsapp_api'].search([]),
#         })

#     @http.route('/ac_ars_hy_whatsapp_api/ac_ars_hy_whatsapp_api/objects/<model("ac_ars_hy_whatsapp_api.ac_ars_hy_whatsapp_api"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ac_ars_hy_whatsapp_api.object', {
#             'object': obj
#         })