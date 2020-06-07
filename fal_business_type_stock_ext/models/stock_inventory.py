from odoo import fields, models, api, _
from odoo.exceptions import AccessError


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    fal_business_type = fields.Many2one(
        'fal.business.type', 'Business Type',
        readonly=True, index=True, required=True,
        states={'draft': [('readonly', False)]},
        default=_get_business_type_default,
        domain="[('company_id', '=', company_id)]")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        # Override This
        if not self.user_has_groups('stock.group_stock_multi_locations'):
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id), ('fal_business_type', '=', self.fal_business_type.id)], limit=1)
            if warehouse:
                self.location_ids = warehouse.lot_stock_id


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    fal_business_type = fields.Many2one(
        'fal.business.type', 'Business Type', related='inventory_id.fal_business_type',
        index=True, readonly=True, store=True)
