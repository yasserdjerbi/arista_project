from odoo import fields, models, api, _
from odoo.exceptions import AccessError


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    fal_business_type = fields.Many2one(
        'fal.business.type', 'Business Type', required=True,
        default=_get_business_type_default, index=True)


class Picking(models.Model):
    _inherit = "stock.picking"

    fal_business_type = fields.Many2one(
        'fal.business.type', string='Business Type', related='picking_type_id.fal_business_type',
        readonly=True, store=True, index=True)
