from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
import logging
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round
from itertools import groupby

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    #################################################################################
    # Override Odoo Button, to call Wizard Instead of just going to entries view
    def action_view_purchase_downpayment(self):
        view_id = self.env['ir.model.data'].xmlid_to_res_id(
            'fal_purchase_downpayment.view_purchase_advance_payment_inv'
        )
        view = {
            'name': _('Down Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.advance.payment.inv',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': True,
            'context': self.env.context
        }
        return view

    #################################################################################
    # Do not copy if line is downpayment
    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'order_line' not in default:
            default['order_line'] = [(0, 0, line.copy_data()[0]) for line in self.order_line.filtered(lambda l: not l.fal_is_downpayment)]
        return super(PurchaseOrder, self).copy_data(default)

    #################################################################################
    # As Odoo doesn't have an invoice preparation from purchase, we create it
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(force_company=self.company_id.id, default_type='in_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': self.partner_ref or '',
            'type': 'in_invoice',
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'user_id': self.user_id and self.user_id.id,
            'partner_id': self.partner_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_payment_ref': self.name,
            'invoice_line_ids': [],
        }
        return invoice_vals

    def _create_invoices(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()
            journal_id = self._context.get('journal_id', False)
            if journal_id:
                invoice_vals['journal_id'] = journal_id.id

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                qty = 0
                if line.product_id.purchase_method == 'purchase':
                    qty = line.product_qty - line.qty_invoiced
                else:
                    qty = line.qty_received - line.qty_invoiced
                if float_is_zero(qty, precision_digits=precision):
                    continue
                if qty > 0 or (qty < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if grouped:
            new_invoice_vals_list = []
            for invoices in groupby(invoice_vals_list, key=lambda x: (x.partner_id.id, x.currency_id.id)):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs),
                    'invoice_origin': ', '.join(origins),
                    'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Manage 'final' parameter: transform out_invoice to out_refund if negative.
        in_invoice_vals_list = []
        refund_bills_vals_list = []
        if final:
            for invoice_vals in invoice_vals_list:
                if sum(l[2]['quantity'] * l[2]['price_unit'] for l in invoice_vals['invoice_line_ids']) < 0:
                    for l in invoice_vals['invoice_line_ids']:
                        l[2]['quantity'] = -l[2]['quantity']
                    invoice_vals['type'] = 'in_refund'
                    refund_bills_vals_list.append(invoice_vals)
                else:
                    in_invoice_vals_list.append(invoice_vals)
        else:
            in_invoice_vals_list = invoice_vals_list

        # Create invoices.
        moves = self.env['account.move'].with_context(default_type='in_invoice').create(in_invoice_vals_list)
        moves += self.env['account.move'].with_context(default_type='in_refund').create(refund_bills_vals_list)
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('purchase_line_id.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    fal_is_downpayment = fields.Boolean(string='Is Deposit Line')

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a purchase order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        qty = 0
        if self.product_id.purchase_method == 'purchase':
            qty = self.product_qty - self.qty_invoiced
        else:
            qty = self.qty_received - self.qty_invoiced
        return {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': qty,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
            'discount': self.discount,
        }
