import base64
from odoo.http import Controller, request, route
from odoo.addons.web.controllers.binary import Binary
from odoo.tools.misc import file_path
from odoo import http


class DasboardBackground(Controller):

    @route(['/dashboard'], type='http', auth="public")
    def dashboard(self, **post):
        user = request.env.user
        company = user.company_id
        if company.bg_image:
            image = base64.b64decode(company.bg_image)
        else:
            return 

        return request.make_response(
            image, [('Content-Type', 'image')])


class KiaBinary(Binary):

    @http.route(['/web/binary/company_logo', '/logo', '/logo.png'], type='http', auth="none", cors="*")
    def company_logo(self, dbname=None, **kw):
        response = super().company_logo(dbname=dbname, **kw)
        try:
            cl = response.headers.get('Content-Length')
            if cl in ['2901', '3261'] or response.status_code != 200:
                kia_logo_path = file_path('custom_login_background/static/src/img/kia_logo.png')
                return http.Stream.from_path(kia_logo_path).get_response()
        except Exception:
            pass
        return response
