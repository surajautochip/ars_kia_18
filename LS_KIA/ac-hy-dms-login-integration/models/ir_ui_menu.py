# -*- coding: utf-8 -*-
from odoo import models, api


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @api.returns('self')
    def get_user_roots(self):
        """
        Overrides the root menu retrieval so that only 'Live Streaming',
        'Camera', 'Apps', and 'Settings' are returned as root applications in the Apps menu.
        All other application menus (default Odoo apps, etc.) are excluded.
        """
        roots = super().get_user_roots()

        # If a user explicitly belongs to the 'Show base Menus' security group,
        # bypass filtering and display all available menus.
        show_base_group = self.env.ref(
            'ac-hy-dms-login-integration.hy_ls_base_menu_hide',
            raise_if_not_found=False
        )
        if show_base_group and self.env.user in show_base_group.users:
            return roots

        allowed_xmlids = [
            'ac_ars_cc_camera.ac_ars_live_streaming_records',
            'ac_ars_ip_camera.ac_ars_ip_camera_main_menu',
            'base.menu_management',
            'base.menu_administration',
        ]

        allowed_menus = self.env['ir.ui.menu'].browse()
        for xmlid in allowed_xmlids:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu:
                allowed_menus |= menu

        # Fallback: if XML IDs could not be resolved, match by menu names
        if not allowed_menus:
            allowed_menus = roots.filtered(
                lambda r: r.name in ('Live Streaming', 'Camera', 'Apps', 'Settings')
            )

        return roots.filtered(lambda r: r.id in allowed_menus.ids)
