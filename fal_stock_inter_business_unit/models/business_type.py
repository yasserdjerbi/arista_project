# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class BusinessType(models.Model):
    _inherit = 'fal.business.type'

    enable_inter_bu_transfer = fields.Boolean(string='Inter Business Unit Transfer', copy=False)
    destination_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    default_picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type')
    apply_transfer_type = fields.Selection([('all', 'Delivery and Receipts'),
                             ('incoming', 'Receipt'),
                             ('outgoing', 'Delivery Order')], string='Apply On', default='all',
                              help="Select the Picking type to apply the inter business unit transfer")
    message = fields.Text(string="Message", compute='compute_message')

    @api.depends('apply_transfer_type', 'destination_warehouse_id')
    def compute_message(self):
        """Creating the Display message according to the selected type."""
        for rec in self:
            if rec.apply_transfer_type == 'incoming':
                create_type = "Delivery"
                selected_type = "Receipt"
            elif rec.apply_transfer_type == 'outgoing':
                create_type = "Receipt"
                selected_type = "Delivery"
            else:
                create_type = "Delivery Order/Receipt"
                selected_type = "Receipt/Delivery"

            msg = _("Create a %s Order when a business unit validate a "
                    "%s Order for %s using %s Warehouse.") % (create_type, selected_type, rec.sudo().name,
                                                    rec.sudo().destination_warehouse_id.name)
            rec.message = msg

    @api.onchange('enable_inter_bu_transfer')
    def onchange_inter_bu_transfer(self):
        business_type = self._origin
        wh = self.env['stock.warehouse'].sudo().search([('fal_business_type', '=', business_type.sudo().id)], limit=1, order='id ASC')
        self.destination_warehouse_id = wh
