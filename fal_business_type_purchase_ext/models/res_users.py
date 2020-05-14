from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.onchange('fal_business_type_ids')
    def _onchnage_business_type(self):
        res = super(ResUsers, self)._onchnage_business_type()
        purchase_rule = self.env.ref('fal_business_type_purchase_ext.purchase_business_type_rule')
        # trigger/recompute rule
        purchase_rule.write({})
        return res
