# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _
from odoo.tools import float_compare, format_datetime


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Need to have this field (even though sale rental have too, to avoid any conflict)
    product_tracking = fields.Selection(related='product_id.tracking')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number', help="Lot/Serial number concerned by the ticket", domain="[('product_id', '=', product_id)]", copy=False)
