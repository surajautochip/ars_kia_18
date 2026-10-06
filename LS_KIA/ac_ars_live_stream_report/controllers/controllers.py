# -*- coding: utf-8 -*-
from odoo import http

# class LiveStreamReport(http.Controller):
#     @http.route('/live_stream_report/live_stream_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/live_stream_report/live_stream_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('live_stream_report.listing', {
#             'root': '/live_stream_report/live_stream_report',
#             'objects': http.request.env['live_stream_report.live_stream_report'].search([]),
#         })

#     @http.route('/live_stream_report/live_stream_report/objects/<model("live_stream_report.live_stream_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('live_stream_report.object', {
#             'object': obj
#         })