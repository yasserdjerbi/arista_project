from odoo import fields, models, api, _
from odoo.exceptions import AccessError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    fal_business_type = fields.Many2one('fal.business.type', 'Business Type', default=_get_business_type_default, index=True, required=True)
