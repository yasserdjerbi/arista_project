# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}


class PurchaseAdvancePaymentInv(models.TransientModel):
    _name = "purchase.advance.payment.inv"
    _description = "Purchase Advance Payment Invoice"

    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('fal_purchase_downpayment.fal_deposit_product_id')
        return self.env['product.product'].browse(int(product_id)).exists()

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id().property_account_expense_id

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().supplier_taxes_id

    @api.model
    def _default_has_down_payment(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
            return purchase_order.order_line.filtered(
                lambda purchase_order_line: purchase_order_line.fal_is_downpayment
            )

        return False

    @api.model
    def _default_currency_id(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
            return purchase_order.currency_id

    @api.model
    def _default_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))
        inv_type = self._context.get('type', 'in_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', [TYPE2JOURNAL[ty] for ty in inv_types if ty in TYPE2JOURNAL]),
            ('company_id', '=', company_id),
        ]
        company_currency_id = self.env['res.company'].browse(company_id).currency_id.id
        currency_id = self._context.get('default_currency_id') or company_currency_id
        currency_clause = [('currency_id', '=', currency_id)]
        if currency_id == company_currency_id:
            currency_clause = ['|', ('currency_id', '=', False)] + currency_clause
        return self.env['account.journal'].search(domain + currency_clause, limit=1)

    advance_payment_method = fields.Selection([
        ('received', 'Regular Bills'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')],
        string='What do you want to be invoiced?',
        default='received',
        required=True
    )
    deduct_down_payments = fields.Boolean('Deduct down payments', default=True)
    has_down_payments = fields.Boolean('Has down payments', default=_default_has_down_payment, readonly=True)
    product_id = fields.Many2one('product.product', string='Down Payment Product', domain=[('type', '=', 'service')], default=_default_product_id)
    count = fields.Integer(default=_count, string='Order Count')
    amount = fields.Float('Down Payment Amount', digits='Account', help="The percentage of amount to be invoiced in advance, taxes excluded.")
    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency_id)
    fixed_amount = fields.Monetary('Down Payment Amount(Fixed)', digits='Account', help="The fixed amount to be invoiced in advance, taxes excluded.")
    deposit_account_id = fields.Many2one("account.account", string="Expense Account", domain=[('deprecated', '=', False)], help="Account used for deposits", default=_default_deposit_account_id)
    deposit_taxes_id = fields.Many2many("account.tax", string="Vendor Taxes", help="Taxes used for deposits", default=_default_deposit_taxes_id)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, default=_default_journal)

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            return {'value': {'amount': 0}}
        return {}

    def _create_invoice(self, order, po_line, amount):
        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.fixed_amount
            name = _('Down Payment')

        invoice_vals = {
            'type': 'in_invoice',
            'invoice_origin': order.name,
            'user_id': order.user_id.id,
            'narration': order.notes,
            'partner_id': order.partner_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': order.currency_id.id,
            'invoice_payment_ref': order.partner_ref,
            'invoice_payment_term_id': order.payment_term_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': po_line.product_uom.id,
                'tax_ids': [(6, 0, po_line.taxes_id.ids)],
                'purchase_line_id': po_line.id,
                'analytic_tag_ids': [(6, 0, po_line.analytic_tag_ids.ids)],
                'analytic_account_id': po_line.account_analytic_id.id or False,
            })],
        }
        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    def create_invoices(self):
        purchase_orders = self.env['purchase.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'received':
            purchase_orders.with_context(journal_id=self.journal_id)._create_invoices(final=self.deduct_down_payments)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('fal_purchase_downpayment.fal_deposit_product_id', self.product_id.id)

            purchase_line_obj = self.env['purchase.order.line']
            for order in purchase_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.fixed_amount
                if self.product_id.purchase_method != 'purchase':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.supplier_taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_id).ids
                else:
                    tax_ids = taxes.ids
                context = {'lang': order.partner_id.lang}
                analytic_tag_ids = []
                for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
                po_line = purchase_line_obj.create({
                    'name': _('Down Payment: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'date_planned': order.date_planned or order.date_order,
                    'product_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'taxes_id': [(6, 0, tax_ids)],
                    'fal_is_downpayment': True,
                })
                del context
                self._create_invoice(order, po_line, amount)
        if self._context.get('open_invoices', False):
            return purchase_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_deposit_product(self):
        return {
            'name': 'Vendor Down payment',
            'type': 'service',
            'purchase_method': 'purchase',
            'property_account_expense_id': self.deposit_account_id.id,
            'supplier_taxes_id': [(6, 0, self.deposit_taxes_id.ids)],
            'company_id': False,
        }
