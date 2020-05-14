from odoo import fields, models, api, _
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]")

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for sale in self:
            if sale.fal_business_type.company_id and sale.company_id:
                if sale.fal_business_type.company_id != sale.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['fal_business_type'] = self.fal_business_type.id
        return res

    @api.model
    def create(self, vals):
        if vals.get('fal_business_type'):
            business_type_obj = self.env['fal.business.type'].browse(vals.get('fal_business_type'))
            sequence_obj = business_type_obj.with_context(company_id=vals['company_id']).generate_sale_sequence()
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = sequence_obj.next_by_id() or _('New')
        return super(SaleOrder, self).create(vals)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", related="order_id.fal_business_type", store=True)


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for sale in self:
            if sale.fal_business_type.company_id and sale.company_id:
                if sale.fal_business_type.company_id != sale.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]")


class SaleReport(models.Model):
    _inherit ='sale.report'

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['fal_business_type'] = ", s.fal_business_type as fal_business_type"
        groupby += ', s.fal_business_type'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)