import logging
_logger = logging.getLogger(__name__)

import odoo
from odoo import http
from odoo.http import request
# from odoo.addons.web.controllers.main import ensure_db, login_and_redirect
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _
import datetime

import odoo
from odoo import http
from odoo.http import request
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _
import datetime


class cust_view_video(http.Controller):

    @http.route('/api/update_stream_status', type='json', auth='public', cors="*", website=True, csrf=False)
    def update_stream_status(self, **post):
        vals = request.get_json_data()
        token = vals.get('token')
        status = vals.get('status')
        if not token or not status:
            return {"status": 400, "message": "Missing token or status"}
        
        live_stream = request.env['ac.ars.live.stream.token'].sudo().search([('token', '=', token)], limit=1)
        if not live_stream:
            return {"status": 404, "message": "Live stream not found"}
        
        allocation = live_stream.dms_ro_number
        
        if status == 'hold' and live_stream.status == 'live':
            live_stream.ac_ars_live_streaming_pause()
            if allocation and allocation.state != 'hold':
                # Bypass the overridden write that triggers pause again
                allocation.with_context(tracking_disable=True).write({'state': 'hold'})
                request.env['bus.bus']._sendone('ac_ars_live_stream_channel', 'stream_updated', {'id': allocation.id})
                
        elif status == 'live' and live_stream.status == 'hold':
            live_stream.ac_ars_live_streaming_resume()
            if allocation and allocation.state != 'live':
                allocation.with_context(tracking_disable=True).write({'state': 'live'})
                request.env['bus.bus']._sendone('ac_ars_live_stream_channel', 'stream_updated', {'id': allocation.id})
                
        return {"status": 200, "message": "Status updated successfully"}


    @http.route('/api/no_view_receive', type='json', auth='public', cors="*", website=True, csrf=False)
    def cust_view_video(self, **post):
        _logger.info("Executing cust_view_video...")
        session_id = False
        vals = request.get_json_data()
        _logger.info("Ping Status: %s", vals)
        db, user, password = vals.get('db', False), vals.get('user', False), vals.get('password', False)
        if db and user and password:
            uid = request.session.authenticate(db, {'login': user, 'password': password, 'type': 'password'})
            live_stream = request.env['ac.ars.live.stream.token'].sudo().search(
                [('token', '=', vals.get('token'))]) if 'token' in vals else False
            if uid:
                if not vals.get('token'):
                    status, message = 300, 'Please send the proper Token'
                else:
                    if vals.get('start_time'):
                        # response_code, message = 'Please send the proper Start Date Time', 300
                        api_token = vals.get('token')
                        token_obj = request.env['ac.ars.live.stream.token'].search([('token', '=', api_token)], limit=1)
                        alloc_obj = token_obj.dms_ro_number if token_obj else None
                        
                        ac_ars_live_streaming = request.env['ac.ars.live.streaming']
                        ac_ars_live_streaming_lines = request.env['ac.ars.live.streaming.line']
                        current_time = fields.Datetime.from_string(fields.Datetime.now())
                        
                        # Fallbacks in case token record is missing/invalid
                        vehicle_no = alloc_obj.dms_ro_no if alloc_obj else api_token
                        cust_name = alloc_obj.partner_id.name if alloc_obj and alloc_obj.partner_id else 'Unknown'
                        dms_ro_number = alloc_obj.id if alloc_obj else False
                        company_id = alloc_obj.company_id.id if alloc_obj and alloc_obj.company_id else False
                        stream_start = alloc_obj.date_start if alloc_obj and alloc_obj.date_start else current_time
                        
                        # Apply timezone offset if stream_start is a string vs datetime object
                        if isinstance(stream_start, str):
                            stream_start = datetime.datetime.strptime(stream_start, DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(hours=5, minutes=30)
                        elif isinstance(stream_start, datetime.datetime):
                            stream_start = stream_start - timedelta(hours=5, minutes=30)
                            
                        live_vals = {'date': current_time, 'name': api_token,
                                     'stream_start_time': stream_start,
                                     'vehicle_no': vehicle_no, 'is_viewing': True,
                                     'cust_name': cust_name,
                                     'dms_ro_number': dms_ro_number,
                                     'company_id': company_id,
                                     'state': 'progress'}
                        ac_ars_live_streaming_id = request.env['ac.ars.live.streaming'].search([('name', '=', api_token)])
                        if not ac_ars_live_streaming_id:
                            stream = ac_ars_live_streaming.create(live_vals)
                            _logger.info("Start Time: %s", vals.get('start_time'))
                            lines = {'line_stream_id': stream.id,
                                     'start_time': datetime.datetime.strptime(vals.get('start_time'),
                                                                              DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(
                                         hours=5, minutes=30)}
                            session_id = ac_ars_live_streaming_lines.create(lines)
                        else:
                            if 'session_id' in vals and vals.get('session_id'):
                                live_id = ac_ars_live_streaming_lines.search(
                                    [('session', '=', vals.get('session_id'))])
                                live_id.write(
                                    {"end_time": datetime.datetime.strptime(vals.get('end_time'),
                                                                            DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(
                                        hours=5, minutes=30)})
                                session_id = live_id
                            else:
                                _logger.info("Start Time: %s", vals.get('start_time'))
                                lines = {'line_stream_id': ac_ars_live_streaming_id.id,
                                         'start_time': datetime.datetime.strptime(vals.get('start_time'),
                                                                                  DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(
                                             hours=5, minutes=30)}
                                session_id = ac_ars_live_streaming_lines.create(lines)
                        status = 200 if uid else 'User Not Found'
                        hold_reason = ''
                        if live_stream.status == 'hold':
                            hold_reason = live_stream.other_reason if live_stream.reason_selection == 'other' else live_stream.reason_selection
                        message, session, token, action = hold_reason if live_stream.status == 'hold' else 'Successfully submitted', session_id, api_token, live_stream.status
                    else:
                        status = 300 if uid else 'User Not Found'
                        message, session, token, action = 'Please send the proper Start Date Time', False, False, live_stream.status
            else:
                status = 400 if uid else 'User Not Found'
                message, session, token, action = 'Invalid Credentials', False, False, live_stream.status
        return {"status": status, "message": message, "session_id": session_id.id, "token": token, "action": action}

    @http.route('/live/customer/review', type='json', auth='public', cors="*", website=True, csrf=False)
    def live_cust_review(self, **post):
        _logger.info("Executing live_cust_review...")
        vals = request.get_json_data()
        try:
            live_record = request.env['ac.ars.live.streaming'].sudo().search([('name', '=', vals.get('token'))], limit=1)
            if live_record and live_record.review:
                if 'review' in vals or 'feedback' in vals:
                    live_record.sudo().write({'review': vals.get('review'), 'feedback': vals.get('feedback')})
                return {'review': live_record.review, 'feedback': live_record.feedback}
            elif live_record:
                if 'review' in vals or 'feedback' in vals:
                    live_record.sudo().write({'review': vals.get('review'), 'feedback': vals.get('feedback')})
                    return {'review': live_record.review, 'feedback': live_record.feedback}
                else:
                    return {'review': "0", 'feedback': ""}
            else:
                return {'review': "0", 'feedback': ""}
        except Exception as e:
            _logger.info(e)


class get_streaming_record(http.Controller):

    @http.route('/api/get_streaming_data', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def get_streaming_record(self, **post):
        _logger.info("Executing get_streaming_record...")
        db, user, password = request.get_json_data().get('db', False), request.get_json_data().get('user',
                                                                                           False), request.get_json_data().get(
            'password', False)
        if db and user and password:
            uid = request.session.authenticate(db, {'login': user, 'password': password, 'type': 'password'})
            if uid:
                dealer_code = request.get_json_data().get('dealer_code')
                _logger.info(request.get_json_data())
                live_report = request.env['live.stream.wizard']
                maninData = live_report.getdelershiplines(dealer_code)
                _logger.info(maninData)
                if maninData != False:
                    message, status, mainDatas, = 'Login and  Successfully Submitted', 200, maninData
                else:
                    message, status, mainDatas, = 'Login But Data Not Found', 200, maninData,
                _logger.info("User Login Successfully")

            else:
                status = 406 if uid else 'User Not Found'
                message, session, token, mainDatas = 'Invalid Credentials', False, False, False
        else:
            status = 404
            message, session, token, mainDatas = 'Invalid Credentials', False, False, False
        return {"status": status, "message": message, "maninData": mainDatas[0], "CamDetails": mainDatas[1]}

    @http.route('/im_livechat/loader/<string:channel_id>', type='http', auth='public')
    def loader(self, channel_id, **kwargs):
        _logger.info("Executing loader...")
        channel_info = request.env['im_livechat.channel'].get_livechat_info_using_token(channel_id)
        # username = kwargs.get("username", _("Visitor"))
        # channel = request.env['im_livechat.channel'].sudo().browse(channel_id)
        # info = request.env['im_livechat.channel'].get_livechat_info(channel.id, username=username)
        return request.render('im_livechat.loader', {'info': channel_info, 'web_session_required': True},
                              headers=[('Content-Type', 'application/javascript')])


class get_streaming_auto_record(http.Controller):

    @http.route('/ac/server/live/stream/save', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def get_streaming_record(self, **post):
        _logger.info("Executing get_streaming_record...")
        dealer_code = request.get_json_data().get('dealer_code')
        record = request.get_json_data().get('record')
        live_stream = request.env['ac.ars.live.streaming.settings']
        company = request.env['res.company'].sudo().search([('dealer_code', '=', dealer_code)], limit=1)
        live_stream_cmp = request.env['ac.ars.live.streaming.settings'].sudo().search([('company_id', '=', company.id)],
                                                                               limit=1)
        res = live_stream.sudo().write_streaming_data(record, company.id)
        live_stream_cmp.write({'port_status': 'online'})
        if res:
            return {"status": 200, "message": "Successfully Submitted", "res": True}
        else:
            return {"status": 406, "message": "Error While Create a Record", "res": False}




