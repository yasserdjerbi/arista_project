# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Need to have this field
    product_tracking = fields.Selection(related='product_id.tracking')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number', help="Lot/Serial number in product", domain="[('product_id', '=', product_id)]", copy=False)

    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for data in res:
            initial_data = [
                (0, 0, {'company_id': self.order_id.company_id.id,
                        'date': self.order_id.date_order,
                        'location_dest_id': self.order_id._get_destination_location(),
                        'location_id': self.order_id.partner_id.property_stock_supplier.id,
                        'product_uom_id': self.product_uom.id,
                        'product_id': self.product_id.id,
                        'picking_id': picking.id,
                        'reference': self.order_id.name})]
            automated_data = [
                (0, 0, {'company_id': self.order_id.company_id.id,
                        'date': self.order_id.date_order,
                        'location_dest_id': self.order_id._get_destination_location(),
                        'location_id': self.order_id.partner_id.property_stock_supplier.id,
                        'lot_id': self.lot_id.id,
                        'qty_done': self.product_uom_qty or 1,
                        'product_uom_id': self.product_uom.id,
                        'product_id': self.product_id.id,
                        'picking_id': picking.id,
                        'reference': self.order_id.name})]
            data['move_line_ids'] = initial_data + automated_data
        return res

    def _prepare_account_move_line(self, move):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals['lot_id'] = self.lot_id
        return vals
