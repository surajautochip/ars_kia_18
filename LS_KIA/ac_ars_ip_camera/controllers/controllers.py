# -*- coding: utf-8 -*-
from odoo import http

# class Ipcam(http.Controller):
#     @http.route('/ipcam/ipcam/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ipcam/ipcam/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ipcam.listing', {
#             'root': '/ipcam/ipcam',
#             'objects': http.request.env['ipcam.ipcam'].search([]),
#         })

#     @http.route('/ipcam/ipcam/objects/<model("ipcam.ipcam"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ipcam.object', {
#             'object': obj
#         })