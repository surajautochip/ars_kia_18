###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import Response, request
import logging

_logger = logging.getLogger(__name__)

class AuthToken(http.Controller):

    @http.route(['/token/<string:page>/<string:token>'], type='http', auth='public', cors="*")
    def consume_sso_token(self, page, token, **post):
        if not token:
            return request.not_found()

        try:
            # Map lookup: Find the user holding this specific single-use token
            user = request.env['res.users'].sudo().search([('dms_token', '=', token)], limit=1)

            if user:
                # Invalidate token immediately to prevent reuse (Single-use security rule)
                user.sudo().write({'dms_token': False})

                # --- PROGRAMMATIC ODOO SESSION INJECTION ---
                request.session.uid = user.id
                request.session.login = user.login

                if hasattr(user, '_compute_session_token'):
                    request.session.session_token = user.sudo()._compute_session_token(request.session.sid)

                if hasattr(request, 'update_env'):
                    request.update_env(user=user.id)

                # --- REDIRECTION ROUTING ---
                if page == 'dashboard':
                    # landing_page = request.env['landing.url'].sudo().search([('name', '=', 'LS Dashboard')], limit=1)
                    # landing_page = False
                    # if landing_page and landing_page.url:
                    #     return request.redirect(landing_page.url)
                    return request.redirect("/")

                elif page == 'planner':
                    return request.redirect('/resource_planner')

                return request.redirect("/")
            else:
                return request.not_found()

        except Exception as e:
            _logger.error("SSO Token Consumption Exception: %s", str(e))
            return request.not_found()



