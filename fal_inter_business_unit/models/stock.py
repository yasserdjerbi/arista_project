# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, registry, SUPERUSER_ID, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        res = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, company_id, values)
        sale_line_id = self.env['sale.order.line'].browse(res.get('sale_line_id'))
        order = sale_line_id.order_id
        business = self.env['fal.business.type']._find_business_from_partner(order.partner_id.id)
        if order.fal_business_type and business:
            picking_type_id = self.env['stock.picking.type'].search([
                ('code', '=', 'internal'), ('warehouse_id', '=', business.warehouse_id.id)
            ], limit=1)
            res.update({
                'picking_type_id': picking_type_id.id,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
            })
        return res
