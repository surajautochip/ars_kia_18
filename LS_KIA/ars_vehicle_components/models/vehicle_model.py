from odoo import models, fields, api


class ars_vehicle_components(models.Model):
    _inherit = 'product.product'

    components_ids = fields.Many2many('product.template')
    product_image_ids = fields.Many2many('vehicle.images')
