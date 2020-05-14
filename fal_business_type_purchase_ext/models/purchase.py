from odoo import fields, models, api, tools, _
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]")

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for purchase in self:
            if purchase.fal_business_type.company_id and purchase.company_id:
                if purchase.fal_business_type.company_id != purchase.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))

    # this function is from fal_purchase_downwpayment to passing the data. no need to depends the module
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res['fal_business_type'] = self.fal_business_type.id
        return res

    @api.model
    def create(self, vals):
        if vals.get('fal_business_type'):
            business_type_obj = self.env['fal.business.type'].browse(vals.get('fal_business_type'))
            sequence_obj = business_type_obj.with_context(company_id=vals['company_id']).generate_purchase_sequence()
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = sequence_obj.next_by_id() or _('New')
        return super(PurchaseOrder, self).create(vals)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", related="order_id.fal_business_type", store=True)


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", readonly=True)

    def _select(self):
        return super(PurchaseReport, self)._select() + ',po.fal_business_type AS fal_business_type'

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ',po.fal_business_type'


class PurchaseBillUnion(models.Model):
    _inherit = 'purchase.bill.union'

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", readonly=True)

    # override method
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'purchase_bill_union')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW purchase_bill_union AS (
                SELECT
                    id, name, ref as reference, partner_id, date, amount_untaxed as amount, currency_id, company_id, fal_business_type,
                    id as vendor_bill_id, NULL as purchase_order_id
                FROM account_move
                WHERE
                    type='in_invoice' and state = 'posted'
            UNION
                SELECT
                    -id, name, partner_ref as reference, partner_id, date_order::date as date, amount_untaxed as amount, currency_id, company_id, fal_business_type,
                    NULL as vendor_bill_id, id as purchase_order_id
                FROM purchase_order
                WHERE
                    state in ('purchase', 'done') AND
                    invoice_status in ('to invoice', 'no')
            )""")
