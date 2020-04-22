from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    account_tbr = fields.Many2one('account.account', required=True, string="Account To be Received", readonly=False,
        domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]")
    account_tbi = fields.Many2one('account.account', required=True, string="Account To be Issued", readonly=False,
        domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]")
