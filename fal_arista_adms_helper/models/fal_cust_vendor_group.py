# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class CustVendGroupBD(models.Model):
    _name = 'x_customer_vendor_group_branch_dependant'
    _description = "Customer Vendor Group Branch Dependant (Account)"

    company_id = fields.Many2one('res.company', string='Company')
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]")
    name = fields.Char("Name")
    property_business_account_receivable_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Receivable",
        domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
        help="This business account will be used instead of the default one as the receivable account for the current partner",)
    property_business_account_payable_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Payable",
        domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
        help="This business account will be used instead of the default one as the payable account for the current partner",)
    property_business_account_titipan_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Titipan",
        help="This business account will be used instead of the default one as the titipan account for the current partner",)
    property_business_account_accrue_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Accrue",
        help="This business account will be used instead of the default one as the accrue account for the current partner",)
