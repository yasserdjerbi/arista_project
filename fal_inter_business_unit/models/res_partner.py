from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_business_account_payable_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Business Account Payable",
        domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
        help="This business account will be used instead of the default one as the payable account for the current partner",)
    property_business_account_receivable_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Business Account Receivable",
        domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
        help="This business account will be used instead of the default one as the receivable account for the current partner",)
    fal_business_partner_account_ids = fields.One2many('business.partner.account', 'partner_id', string="Business Account")


class BusinessPartnerAccount(models.Model):
    _name = 'business.partner.account'

    partner_id = fields.Many2one('res.partner', 'Partner', domain="[('is_business_partner', '=', True)]")
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type")
    property_business_account_payable_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Payable",
        domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
        help="This business account will be used instead of the default one as the payable account for the current partner",)
    property_business_account_receivable_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Receivable",
        domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
        help="This business account will be used instead of the default one as the receivable account for the current partner",)
