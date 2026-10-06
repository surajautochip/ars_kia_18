###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    def _create_user(self):
        _logger.info("Executing _create_user...")
        user = super()._create_user()
        user._set_default_token()
        return user
