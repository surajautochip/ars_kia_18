# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ars_vehicle_image(models.Model):
    _name = 'vehicle.images'

    name = fields.Char('Name')
    image_medium = fields.Binary('Image')
    model_id = fields.Many2one('product.product')
    # coordinates = fields.Char('Co ordinates')
    component_ids = fields.One2many('vehicle.components', 'vh_image_id')
    website_published = fields.Boolean("Website Published", default=True)


class ars_vehicle_components(models.Model):
    _name = 'vehicle.components'

    name = fields.Char('Name')
    coordinates = fields.Char('Co ordinates')
    component_id = fields.Many2one('product.template')
    parts_ids = fields.Many2many('product.template')
    vh_image_id = fields.Many2one('vehicle.images')
    description = fields.Char('Description')
