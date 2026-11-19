# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(IrHttp, self).session_info()
        if not result.get('home_action_id'):
            dashboard_action = self.env.ref('ac_ars_live_stream_dashboard.action_ac_ars_live_stream_dashboard', raise_if_not_found=False)
            if dashboard_action:
                result['home_action_id'] = dashboard_action.id
        return result
