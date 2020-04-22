from odoo import fields, models, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'


    journal_tbi = fields.Many2one('account.move', string='Journal To Be Issued', readonly=True, copy=False)

    def act_to_be_issued(self):
        created_move = self.env['account.move']
        line_list = []
        for move in self:
            self_currency = move.currency_id.id
            company_currency = move.company_id.currency_id
            if move.currency_id == company_currency:
                # Single-currency.
                self_currency = False
                amount_currency = 0.0
                amount = move.amount_total
            else:
                # Multi-currencies.
                amount_currency = move.amount_total
                amount = move.currency_id._convert(amount_currency, company_currency.id, move.company_id)

            move_line_1 = {
                'name': move.name,
                'account_id': move.company_id.account_tbi.id if move.type in ['out_invoice', 'out_refund'] else move.company_id.account_tbr.id,
                'debit': 0.0 if move.type in ['out_invoice', 'out_refund'] else amount,
                'credit': amount if move.type in ['out_invoice', 'out_refund'] else 0.0,
                'journal_id': move.journal_id.id,
                'currency_id': self_currency,
                'amount_currency': -1 * amount_currency if move.type in ['out_invoice', 'out_refund'] else amount_currency,
                'product_uom_id': 1
            }
            line_list.append((0, 0, move_line_1))

            move_line_2 = {
                'name': move.name,
                'account_id': move.partner_id.property_account_receivable_id.id if move.type in ['out_invoice', 'out_refund'] else move.partner_id.property_account_payable_id.id,
                'debit': amount if move.type in ['out_invoice', 'out_refund'] else 0.0,
                'credit': 0.0 if move.type in ['out_invoice', 'out_refund'] else amount,
                'journal_id': move.journal_id.id,
                'currency_id': self_currency,
                'amount_currency': amount_currency if move.type in ['out_invoice', 'out_refund'] else -1 * amount_currency,
                'product_uom_id': 1
            }
            line_list.append((0, 0, move_line_2))

            move_vals = {
                'type': 'entry',
                'ref': move.name,
                'date': move.invoice_date or fields.Datetime.today(),
                'journal_id': self.journal_id.id,
                'line_ids': line_list,
            }

            acc_move = created_move.create(move_vals)
            move.journal_tbi = acc_move.id



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            move = self.env['account.move'].browse(vals.get('move_id'))
            move_type = move.type
            account = self.env['account.account'].browse(vals.get('account_id'))
            if move_type == 'in_invoice':
                tbr = move.company_id.account_tbr
                if tbr:
                    if account.user_type_id.type == 'receivable':
                        vals['account_id'] = tbr.id
            elif move_type == 'out_invoice':
                tbi = move.company_id.account_tbi
                if tbi:
                    if account.user_type_id.type == 'payable':
                        vals['account_id'] = tbi.id
        moves = super(AccountMoveLine, self).create(vals_list)

        return moves