# -*- coding: utf-8 -*-
from odoo import http

# class ArsVehicleComponents(http.Controller):
#     @http.route('/ars_vehicle_components/ars_vehicle_components/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ars_vehicle_components/ars_vehicle_components/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ars_vehicle_components.listing', {
#             'root': '/ars_vehicle_components/ars_vehicle_components',
#             'objects': http.request.env['ars_vehicle_components.ars_vehicle_components'].search([]),
#         })

#     @http.route('/ars_vehicle_components/ars_vehicle_components/objects/<model("ars_vehicle_components.ars_vehicle_components"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ars_vehicle_components.object', {
#             'object': obj
#         })