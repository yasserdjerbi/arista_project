# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    auto_generated = fields.Boolean(string='Auto Generated Transfer', copy=False,
                                    help="Field helps to check the picking is created from an another picking or not")

    def button_validate(self):
        """Creating the internal transfer if it is not created from another picking"""
        res = super(StockPickingInherit, self).button_validate()
        if not self.auto_generated:
            self.create_interbu_transfer()
        return res

    def create_interbu_transfer(self):
        """Creating the transfer if the selected business unit is enabled the internal transfer option"""
        bu_id = self.env['fal.business.type'].sudo().search([('partner_id', '=', self.partner_id.id)], limit=1)
        operation_type_id = False
        location_id = False
        location_dest_id = False

        if bu_id and bu_id.enable_inter_bu_transfer:
            create_transfer = False
            if self.picking_type_id.code == bu_id.apply_transfer_type or bu_id.apply_transfer_type == 'all':
                create_transfer = True
            if create_transfer:
                warehouse_ids = bu_id.destination_warehouse_id.sudo()
                if bu_id.default_picking_type_id:
                    operation_type_id = bu_id.default_picking_type_id
                elif self.picking_type_id.code == 'incoming':
                    operation_type_id = self.env['stock.picking.type'].sudo().search(
                        [('warehouse_id', 'in', warehouse_ids.ids), ('code', '=', 'outgoing')], limit=1)

                elif self.picking_type_id.code == 'outgoing':
                    operation_type_id = self.env['stock.picking.type'].sudo().search(
                        [('warehouse_id', 'in', warehouse_ids.ids), ('code', '=', 'incoming')], limit=1)
                else:
                    raise UserError(_('Internal transfer between business unit are not allowed'))

                if operation_type_id:
                    if operation_type_id.default_location_src_id:
                        location_id = operation_type_id.default_location_src_id.id
                    elif self.fal_business_type.partner_id:
                        location_id = self.partner_id.property_stock_supplier.id

                    if operation_type_id.default_location_dest_id:
                        location_dest_id = operation_type_id.default_location_dest_id.id
                    elif bu_id.partner_id:
                        location_dest_id = bu_id.partner_id.property_stock_customer.id
                if location_id and location_dest_id:
                    picking_vals = {
                        'partner_id': self.fal_business_type.partner_id.id,
                        'company_id': bu_id.company_id.id,
                        'fal_business_type': bu_id.id,
                        'picking_type_id': operation_type_id.id,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'auto_generated': True,
                        'origin': self.name
                    }
                    picking_id = self.env['stock.picking'].sudo().create(picking_vals)
                else:
                    raise UserError(_('Please configure appropriate locations on Operation type/Partner'))

                for move in self.move_lines:
                    lines = self.move_line_ids.filtered(lambda x: x.product_id == move.product_id)
                    done_qty = sum(lines.mapped('qty_done'))
                    if not done_qty:
                        done_qty = sum(lines.mapped('product_uom_qty'))
                    svl = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)], limit=1)
                    move_vals = {
                        'picking_id': picking_id.id,
                        'picking_type_id': operation_type_id.id,
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'product_uom': move.product_uom.id,
                        'product_uom_qty': done_qty,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'company_id': bu_id.company_id.id,
                        'fal_business_type': bu_id.id,
                        'price_unit': svl and abs(svl.value) or 0,
                    }
                    self.env['stock.move'].sudo().create(move_vals)
                if picking_id:
                    picking_id.sudo().action_confirm()
                    picking_id.sudo().action_assign()
