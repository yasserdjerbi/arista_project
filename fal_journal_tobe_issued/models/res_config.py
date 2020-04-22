# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    account_tbi = fields.Many2one('account.account',
        string="Account To Be Issued",
        related='company_id.account_tbi',
        readonly=False)

    account_tbr = fields.Many2one('account.account',
        string="Account To Be Received",
        related='company_id.account_tbr',
        readonly=False)
