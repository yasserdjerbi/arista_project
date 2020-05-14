# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class sale_order(models.Model):
    _inherit = "sale.order"

    auto_generated = fields.Boolean(string='Auto Generated Sales Order', copy=False)

    def _action_confirm(self):
        """ Generate inter business purchase order based on conditions """
        res = super(sale_order, self)._action_confirm()
        for order in self:
            if not order.fal_business_type: # if business unit not found, return to normal behavior
                continue
            if not order.company_id: # if company not found, return to normal behavior
                continue
            # if business unit allow to create a Purchase Order from Sales Order, then do it !
            business = self.env['fal.business.type']._find_business_from_partner(order.partner_id.id)
            if business and business.applicable_on in ('sale', 'sale_purchase') and (not order.auto_generated):
                order.inter_business_create_purchase_order(business, business.company_id)
        return res


    def inter_business_create_purchase_order(self, business, company):
        """ Create a Purchase Order from the current SO (self)
            Note : In this method, reading the current SO is done as sudo, and the creation of the derived
            PO as intercompany_user, minimizing the access right required for the trigger user
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id, company_id=company.id)
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        for rec in self:
            # find user for creating and validating SO/PO from business unit
            interbusiness_uid = business.interbusiness_user_id and business.interbusiness_user_id.id or False
            if not interbusiness_uid:
                raise Warning(_('Provide one user for interbusiness relation for % ') % business.name)
            # check interbusiness user access rights
            if not PurchaseOrder.with_user(interbusiness_uid).check_access_rights('create', raise_exception=False):
                raise Warning(_("Inter business user of business unit %s doesn't have enough access rights") % business.name)

            business_partner = rec.fal_business_type.partner_id.with_user(interbusiness_uid)
            # create the PO and generate its lines from the SO
            # read it as sudo, because inter-compagny user can not have the access right on PO
            po_vals = rec.sudo()._prepare_purchase_order_data_business(business, company, business_partner)

            inter_user = self.env['res.users'].sudo().browse(interbusiness_uid)
            purchase_order = PurchaseOrder.with_context(allowed_business_type_ids=inter_user.fal_business_type_ids.ids).with_user(interbusiness_uid).create(po_vals)
            for line in rec.order_line.sudo().filtered(lambda l: not l.display_type):
                po_line_vals = rec._prepare_purchase_order_line_data_business(line, rec.date_order,
                    purchase_order.id, company, business)
                # TODO: create can be done in batch; this may be a performance bottleneck
                PurchaseOrderLine.with_user(interbusiness_uid).with_context(allowed_business_type_ids=inter_user.fal_business_type_ids.ids).create(po_line_vals)

            # write customer reference field on SO
            if not rec.client_order_ref:
                rec.client_order_ref = purchase_order.name

            # auto-validate the purchase order if needed
            if business.auto_validation:
                purchase_order.with_user(interbusiness_uid).button_confirm()


    def _prepare_purchase_order_data_business(self, business, company, business_partner):
        """ Generate purchase order values, from the SO (self)
            :param company_partner : the partner representing the company of the SO
            :rtype company_partner : res.partner record
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        self.ensure_one()
        # find location and warehouse, pick warehouse from company object
        warehouse = business.warehouse_id or False
        if not warehouse:
            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))
        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'), ('warehouse_id', '=', warehouse.id)
        ], limit=1)

        sequence_obj = business.with_context(company_id=company.id).generate_purchase_sequence()

        return {
            'name': sequence_obj.next_by_id(),
            'origin': self.name,
            'partner_id': business_partner.id,
            'picking_type_id': picking_type_id.id,
            'date_order': self.date_order,
            'company_id': company.id,
            'fiscal_position_id': business_partner.property_account_position_id.id,
            'payment_term_id': business_partner.property_supplier_payment_term_id.id,
            'auto_generated': True,
            'partner_ref': self.name,
            'currency_id': self.currency_id.id,
            'fal_business_type': business.id
        }

    @api.model
    def _prepare_purchase_order_line_data_business(self, so_line, date_order, purchase_id, company, business):
        # price on PO so_line should be so_line - discount
        price = so_line.price_unit - (so_line.price_unit * (so_line.discount / 100))

        # computing Default taxes of so_line. It may not affect because of parallel company relation
        taxes = so_line.tax_id
        if so_line.product_id:
            taxes = so_line.product_id.supplier_taxes_id

        # fetch taxes by company not by inter-company user
        company_taxes = taxes.filtered(lambda t: t.company_id == company)
        if purchase_id:
            po = self.env["purchase.order"].with_user(business.interbusiness_user_id).browse(purchase_id)
            company_taxes = po.fiscal_position_id.map_tax(company_taxes, so_line.product_id, po.partner_id)

        quantity = so_line.product_id and so_line.product_uom._compute_quantity(so_line.product_uom_qty, so_line.product_id.uom_po_id) or so_line.product_uom_qty
        price = so_line.product_id and so_line.product_uom._compute_price(price, so_line.product_id.uom_po_id) or price
        return {
            'name': so_line.name,
            'order_id': purchase_id,
            'product_qty': quantity,
            'product_id': so_line.product_id and so_line.product_id.id or False,
            'product_uom': so_line.product_id and so_line.product_id.uom_po_id.id or so_line.product_uom.id,
            'price_unit': price or 0.0,
            'company_id': company.id,
            'date_planned': so_line.order_id.expected_date or date_order,
            'taxes_id': [(6, 0, company_taxes.ids)],
        }
