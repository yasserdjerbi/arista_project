# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class ProductDimension(models.Model):
    _name = 'x_product_dimension'
    _description = "Product Dimension (Account)"

    name = fields.Char("Name")
