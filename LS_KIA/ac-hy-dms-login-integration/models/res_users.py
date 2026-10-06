###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
_logger = logging.getLogger(__name__)

import random
import string

from odoo import _, api, exceptions, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_default_token(self):
        _logger.info("Executing _get_default_token...")
        _logger.info("tttttttttttttttttttttt")
        return ''.join(
            random.choice(
                string.ascii_uppercase + string.digits
            ) for i in range(1, 33))

    token = fields.Char(
        string='Token',
        help='Alphanumeric key to login into Odoo',
    )

    dms_uid = fields.Char(string="DMS UID")
    dms_token = fields.Char(string="DMS TOKEN")
    dms_auth_token = fields.Char(string="DMS AUTH TOKEN")

    def _set_default_token(self):
        _logger.info("Executing _set_default_token...")
        self.token = self._get_default_token()

    @api.constrains('token')
    def _check_token_unique(self):
        _logger.info("Executing _check_token_unique...")
        ids = self.search([
            ('id', '!=', self.id),
            ('token', '=', self.token),
        ])
        if ids:
            raise exceptions.ValidationError(_('User token must be unique'))

    def ls_set_user_permission(self):
        _logger.info("Executing ls_set_user_permission...")
        category_names = [
            'Sales', 'Project', 'Timesheets', 'Recruitment', 'Live Support', 'Employees', 'Website',
            'Accounting & Finance', 'Purchases', 'Inventory', 'Mass Mailing', 'Fleet', 'Survey'
        ]
        categories = self.env['ir.module.category'].sudo().search([('name', 'in', category_names)])
        groups = self.env['res.groups'].sudo().search([('category_id', 'in', categories.ids)])
        
        commands = [(3, g.id) for g in groups]
        if commands:
            self.sudo().write({'groups_id': commands})
            
        ls_group = self.env.ref("ac_ars_cc_camera.live_stream_group_manager", raise_if_not_found=False)
        if ls_group:
            ls_group.sudo().write({'users': [(4, self.id)]})
        return True
