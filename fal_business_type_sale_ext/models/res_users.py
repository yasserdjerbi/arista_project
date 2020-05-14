from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.onchange('fal_business_type_ids')
    def _onchnage_business_type(self):
        res = super(ResUsers, self)._onchnage_business_type()
        crm_rule = self.env.ref('fal_business_type_sale_ext.sale_business_type_rule')
        # trigger/recompute rule
        crm_rule.write({})
        return res
