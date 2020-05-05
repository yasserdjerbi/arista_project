# -*- coding: utf-8 -*-
# Part of Cluedoo.

from odoo import fields, models, tools


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
