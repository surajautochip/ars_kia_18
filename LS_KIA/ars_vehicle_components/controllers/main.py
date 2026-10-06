import logging
_logger = logging.getLogger(__name__)

import werkzeug.utils
from odoo import http
from odoo.http import request
from odoo.addons import auth_signup
from odoo.exceptions import UserError
from odoo.addons.website.controllers.main import Website



class product_component_controllers(http.Controller):

    @http.route(['/live/token/product/components'], type='json', auth='public', methods=['POST'],
                cors="*", website=True, csrf=False)
    def expose_product_components(self, **post):
        _logger.info("Executing expose_product_components...")
        try:
            if 'token' in request.get_json_data():
                api_token = request.get_json_data().get('token')
                live_token = request.env['ac.ars.live.stream.token'].sudo().search([('token', '=', api_token)], limit=1)
                if live_token:
                    allocation_data = live_token.dms_ro_number
                
                    product = allocation_data.product_id
                    vals = []
                    url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    # / web / image?model = product.product & id = 143 & field = image
                    for prod in product.product_image_ids:
                        comp = []
                        for components in prod.component_ids:
                            parts = []
                            for part in components.parts_ids:
                                parts_url = url + '/web/image?model=' + str(
                                    part._name) + '&id=' + str(part.id) + '&field=image'
                                parts.append([{'name': part.name, 'image': parts_url}])
                            comp.append({'name': components.name, 'coordinates': components.coordinates,
                                         'description': components.description, 'components': parts})
                        product_url = url + '/web/image?model=' + str(prod._name) + '&id=' + str(
                            prod.id) + '&field=image_medium'
                        vals.append({'name': prod.name, 'image': product_url,
                                     'body_parts': comp})
                    return vals
            return True
        except Exception as e:
            _logger.info(e)
            return False

    @http.route(['/live/token/stages'], type='json', auth='public', methods=['POST'],
                cors="*", website=True, csrf=False)
    def get_vehicle_stages(self, **post):
        _logger.info("Executing get_vehicle_stages...")
        try:
            if 'token' in request.get_json_data():
                api_token = request.get_json_data().get('token')
                token = request.env['ac.ars.live.streaming'].sudo().search([('name', '=', api_token)])
                live_token = request.env['ac.ars.live.stream.token'].sudo().search([('token', '=', api_token)], limit=1)
                # so = request.env['sale.order'].sudo().search([('id', '=', events_id.res_id)])
                vals = []
                stages = ['Work Start (At bay)', 'Work Progress', 'Work Complete (At bay)']
                if live_token:
                    vals.append([{'vehicleNumber': live_token.dms_ro_number.dms_ro_no if live_token.dms_ro_number else 'Unknown'}])
                    status_stage = 'completed'
                    if live_token.status == 'live':
                        for stage in stages:
                            if stage == 'Work Start (At bay)':
                                status_stage = 'completed'
                            elif stage == 'Work Progress':
                                status_stage = 'Work In Progress'
                            elif stage == 'Work Complete (At bay)':
                                status_stage = 'pending'
                            vals.append([{'stage': stage, 'status': status_stage}])
                    else:
                        for stage in stages:
                            status_stage = 'completed'
                            vals.append([{'stage': stage, 'status': status_stage}])

                    _logger.info('Vehicle Details: %s %s', api_token, vals)
                return vals
        except Exception as e:
            _logger.info(e)
            return False

