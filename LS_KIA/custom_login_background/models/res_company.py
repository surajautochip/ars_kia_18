

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    bg_image = fields.Binary(
        string="Login Background Image", 
        help="To avoid stretching and maintain a high-quality look, we recommend uploading an image with a resolution of 1920x1080 pixels (16:9 aspect ratio)."
    )
