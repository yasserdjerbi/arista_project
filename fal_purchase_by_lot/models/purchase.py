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
    po_lot_ids = fields.One2many('purchase.order.line.lot', 'po_line_id', string='Lot/Serial Number', help="Lot/Serial number in product", copy=False, domain="[('po_line_id', '=', False)]")

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
                        'lot_name': po_lot_id.lot,
                        'qty_done': po_lot_id.qty or 1,
                        'product_uom_id': self.product_uom.id,
                        'product_id': self.product_id.id,
                        'picking_id': picking.id,
                        'reference': self.order_id.name,
                        }) for po_lot_id in self.po_lot_ids]
            data['move_line_ids'] = initial_data + automated_data
        return res


class PurchaseOrderLineLot(models.Model):
    _name = 'purchase.order.line.lot'

    @api.depends('lot', 'qty')
    def name_get(self):
        res = super(PurchaseOrderLineLot, self).name_get()
        new_res = []
        for item in res:
            poll = self.browse(item[0])
            new_name = poll.lot + " : " + str(poll.qty)
            if self.env.user.has_group('uom.group_uom'):
                new_name = new_name + ' ' + (poll.po_line_id.product_uom.name or '')
            new_res.append((item[0], new_name))
        return new_res

    po_line_id = fields.Many2one('purchase.order.line', 'PO Line')
    product_tracking = fields.Char('Product Tracking')
    lot = fields.Char("Lot/SN", required=True)
    qty = fields.Float("Qty", default=1, required=True)

    @api.constrains('qty')
    def _check_qty(self):
        for poll in self:
            if poll.qty < 1:
                raise UserError(_(
                    'Error!\nQty cannot be lower than 1.'))

    @api.constrains('qty', 'product_tracking')
    def _check_tracking(self):
        for poll in self:
            if poll.product_tracking == 'serial' and poll.qty != 1:
                raise UserError(_(
                    'Error!\nQty for Product Tracking by Serial must be 1.'))
