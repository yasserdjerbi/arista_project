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
