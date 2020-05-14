# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class AccountMove(models.Model):
    _inherit = 'account.move'

    auto_generated = fields.Boolean(string='Auto Generated Document', copy=False, default=False)

    @api.onchange('fal_business_type')
    def _onchange_business_type(self):
        move_type = self._context.get('default_type', 'entry')
        journal_type = 'general'
        if move_type in self.get_sale_types(include_receipts=True):
            journal_type = 'sale'
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_type = 'purchase'

        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [
            ('company_id', '=', company_id),
            ('type', '=', journal_type),
        ]
        journal = None
        if self.fal_business_type:
            journal = self.env['account.journal'].search(domain + [('fal_business_type', '=', self.fal_business_type.id)], limit=1)

            if self._context.get('default_currency_id'):
                currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
                journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        self.journal_id = journal.id

    def post(self):
        # OVERRIDE to generate cross invoice based on company rules.
        invoices_map = {}
        for invoice in self.filtered(lambda move: move.is_invoice()):
            business = self.env['fal.business.type']._find_business_from_partner(invoice.partner_id.id)
            if business and business.rule_type == 'invoice_and_refund' and not invoice.auto_generated:
                invoices_map.setdefault(business.company_id, self.env['account.move'])
                invoices_map[business.company_id] += invoice
        for company, invoices in invoices_map.items():
            invoices._inter_business_create_invoices(company, business)
        return super(AccountMove, self).post()

    def _inter_business_create_invoices(self, company, business):
        ''' Create cross company invoices.
        :param company: The targeted new company (res.company record).
        :return:        The newly created invoices.
        '''
        invoices_ctx = self.with_user(business.interbusiness_user_id).with_context(default_company_id=company.id, force_company=company.id)

        # Prepare invoice values.
        invoices_vals_per_type = {}
        inverse_types = {
            'in_invoice': 'out_invoice',
            'in_refund': 'out_refund',
            'out_invoice': 'in_invoice',
            'out_refund': 'in_refund',
        }
        for inv in invoices_ctx:
            invoice_vals = inv._inter_business_prepare_invoice_data(company, business, inverse_types[inv.type])
            invoice_vals['invoice_line_ids'] = []
            for line in inv.invoice_line_ids:
                invoice_vals['invoice_line_ids'].append((0, 0, line._inter_business_prepare_invoice_line_data(company, business)))

            inv_new = inv.new(invoice_vals)
            for line in inv_new.invoice_line_ids:
                line.tax_ids = line._get_computed_taxes()
            invoice_vals = inv_new._convert_to_write(inv_new._cache)
            invoice_vals.pop('line_ids', None)

            invoices_vals_per_type.setdefault(invoice_vals['type'], [])
            invoices_vals_per_type[invoice_vals['type']].append(invoice_vals)

        # Create invoices.
        moves = None
        for invoice_type, invoices_vals in invoices_vals_per_type.items():
            invoices = invoices_ctx.with_context(default_type=invoice_type).create(invoices_vals)
            if moves:
                moves += invoices
            else:
                moves = invoices
        return moves

    def _inter_business_prepare_invoice_data(self, company, business, invoice_type):
        ''' Get values to create the invoice.
        /!\ Doesn't care about lines, see '_inter_company_prepare_invoice_line_data'.
        :param company: The targeted company.
        :return: Python dictionary of values.
        '''
        self.ensure_one()
        return {
            'type': invoice_type,
            'ref': self.ref,
            'fal_business_type': business.id,
            'partner_id': self.fal_business_type.partner_id.id,
            'currency_id': self.currency_id.id,
            'auto_generated': True,
            'invoice_date': self.invoice_date,
            'invoice_payment_ref': self.invoice_payment_ref,
            'invoice_origin': _('%s Invoice: %s') % (self.company_id.name, self.name),
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _inter_business_prepare_invoice_line_data(self, company, business):
        ''' Get values to create the invoice line.
        :param company: The targeted company.
        :return: Python dictionary of values.
        '''
        self.ensure_one()

        return {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': self.quantity,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _fal_get_move_values(self):
        for payment in self:
            business_type = payment.invoice_ids.mapped('fal_business_type')
            company_currency = payment.company_id.currency_id
            business_partner = business_type.partner_id.fal_business_partner_account_ids.filtered(
                lambda a: a.fal_business_type.partner_id == payment.journal_id.fal_business_type.partner_id)

            # Compute amounts.
            write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
            if payment.payment_type in ('outbound', 'transfer'):
                counterpart_amount = payment.amount
                liquidity_line_account = payment.journal_id.default_debit_account_id
                account = business_partner.property_business_account_payable_id
            else:
                counterpart_amount = -payment.amount
                liquidity_line_account = payment.journal_id.default_credit_account_id
                account = business_partner.property_business_account_receivable_id

            # Manage currency.
            if payment.currency_id == company_currency:
                # Single-currency.
                balance = counterpart_amount
                write_off_balance = write_off_amount
                counterpart_amount = write_off_amount = 0.0
                currency_id = False
            else:
                # Multi-currencies.
                balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
                write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
                currency_id = payment.currency_id.id

            # Manage custom currency on journal for liquidity line.
            if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                # Custom currency on journal.
                if payment.journal_id.currency_id == company_currency:
                    # Single-currency
                    liquidity_line_currency_id = False
                else:
                    liquidity_line_currency_id = payment.journal_id.currency_id.id
                liquidity_amount = company_currency._convert(
                    balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                liquidity_amount = counterpart_amount

            # Compute 'name' to be used in receivable/payable line.
            rec_pay_line_name = ''
            if payment.payment_type == 'transfer':
                rec_pay_line_name = payment.name
            else:
                if payment.partner_type == 'customer':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Customer Payment")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Customer Credit Note")
                elif payment.partner_type == 'supplier':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Vendor Credit Note")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Vendor Payment")
                if payment.invoice_ids:
                    rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

            liquidity_line_name = payment.name

            # ==== 'inbound' / 'outbound' ====

            move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'journal_id': payment.journal_id.id,
                'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                'partner_id': payment.partner_id.id,
                'fal_business_type': payment.journal_id.fal_business_type.id,
                'line_ids': [
                    # Receivable / Payable / Transfer line.
                    (0, 0, {
                        'name': rec_pay_line_name,
                        'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                        'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.id,
                        'account_id': account.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity line.
                    (0, 0, {
                        'name': liquidity_line_name,
                        'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.id,
                        'account_id': liquidity_line_account.id,
                        'payment_id': payment.id,
                    }),
                ],
            }

            if write_off_balance:
                # Write-off line.
                move_vals['line_ids'].append((0, 0, {
                    'name': payment.writeoff_label,
                    'amount_currency': -write_off_amount,
                    'currency_id': currency_id,
                    'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                    'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.id,
                    'account_id': payment.writeoff_account_id.id,
                    'payment_id': payment.id,
                }))

        return move_vals

    def _prepare_payment_moves(self):
        res = super(AccountPayment, self)._prepare_payment_moves()
        for rec in self:
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            business_type = rec.invoice_ids.mapped('fal_business_type')
            # change account to inter business account
            if rec.journal_id.fal_business_type and business_type and business_type != rec.journal_id.fal_business_type:
                business_partner = rec.journal_id.fal_business_type.partner_id.fal_business_partner_account_ids.filtered(
                    lambda a: a.fal_business_type == business_type)
                if rec.payment_type in ('outbound', 'transfer'):
                    liquidity_line_account = rec.journal_id.default_debit_account_id
                    account = business_partner.property_business_account_payable_id
                else:
                    liquidity_line_account = rec.journal_id.default_credit_account_id
                    account = business_partner.property_business_account_receivable_id
                lines = res[0].get('line_ids')
                for line in lines:
                    if line[2].get('account_id') == liquidity_line_account.id:
                        line[2].update({'account_id': account.id})

                move = AccountMove.create(rec._fal_get_move_values())
                move.post()
        return res
