# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class ReasonADMS(models.Model):
    _name = 'x_reason_adms'
    _description = "Reason Company Dependant (Account)"

    company_id = fields.Many2one('res.company', string='Company')
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]")
    name = fields.Char("Name")
    property_account_reason_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Receivable")
