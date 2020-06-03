from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_business_partner = fields.Boolean('Business Partner')
    fal_business_type = fields.Many2one('fal.business.type', 'Business Type', index=True, domain="[('company_id', '=', company_id)]")
