# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class ReasonADMS(models.Model):
    _name = 'x_reason_adms'
    _description = "Reason Company Dependant (Account)"

    name = fields.Char("Name")
    property_account_reason_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Receivable")
