# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_titipan_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Titipan",
        help="This business account will be used instead of the default one as the titipan account for the current partner",)
