from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_business_partner = fields.Boolean('Business Partner')
