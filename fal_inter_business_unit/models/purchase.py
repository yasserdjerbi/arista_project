# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    auto_generated = fields.Boolean(string='Auto Generated Purchase Order', copy=False)

    def _get_default_internal_picking_type(self, warehouse):
        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'), ('warehouse_id', '=', warehouse.id)
        ], limit=1)
        return picking_type_id

    def button_approve(self, force=False):
        """ Generate inter company sales order base on conditions."""
        res = super(PurchaseOrder, self).button_approve(force=force)
        for order in self:
            # get the company from partner then trigger action of intercompany relation
            business = self.env['fal.business.type']._find_business_from_partner(order.partner_id.id)
            warehouse = order.fal_business_type and order.fal_business_type.warehouse_id or False
            if business and warehouse:
                picking_type_id = self._get_default_internal_picking_type(warehouse)
                order.picking_type_id = picking_type_id.id
            if business and business.applicable_on in ('purchase', 'sale_purchase') and (not order.auto_generated):
                order.inter_business_create_sale_order(business, business.company_id)
        return res


    def inter_business_create_sale_order(self, business, company):
        self = self.with_context(force_company=company.id)
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']

        # find user for creating and validation SO/PO from partner company
        interbusiness_uid = business.interbusiness_user_id and business.interbusiness_user_id.id or False
        if not interbusiness_uid:
            raise Warning(_('Provide at least one user for inter business relation for % ') % business.name)
        # check intercompany user access rights
        if not SaleOrder.with_user(interbusiness_uid).check_access_rights('create', raise_exception=False):
            raise Warning(_("Inter business user of business unit %s doesn't have enough access rights") % business.name)

        for rec in self:
            business_partner = rec.fal_business_type.partner_id.with_user(interbusiness_uid)

            # create the SO and generate its lines from the PO lines
            # read it as sudo, because inter-compagny user can not have the access right on PO
            sale_order_data = rec.sudo()._prepare_sale_order_data_business(
                rec.name, business_partner, business, company,
                rec.dest_address_id and rec.dest_address_id.id or False)
            inter_user = self.env['res.users'].sudo().browse(interbusiness_uid)
            sale_order = SaleOrder.with_context(allowed_business_ids=inter_user.fal_business_type_ids.ids).with_user(interbusiness_uid).create(sale_order_data)
            # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
            for line in rec.order_line.sudo():
                so_line_vals = rec._prepare_sale_order_line_data_business(line, business, company, sale_order.id)
                # TODO: create can be done in batch; this may be a performance bottleneck
                SaleOrderLine.with_user(interbusiness_uid).with_context(allowed_business_ids=inter_user.fal_business_type_ids.ids).create(so_line_vals)

            # write vendor reference field on PO
            if not rec.partner_ref:
                rec.partner_ref = sale_order.name

            #Validation of sales order
            if business.auto_validation:
                sale_order.with_user(interbusiness_uid).action_confirm()

    def _prepare_sale_order_data_business(self, name, partner, business, company, direct_delivery_address):
        """ Generate the Sales Order values from the PO
            :param name : the origin client reference
            :rtype name : string
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param direct_delivery_address : the address of the SO
            :rtype direct_delivery_address : res.partner record
        """
        self.ensure_one()
        partner_addr = partner.sudo().address_get(['invoice', 'delivery', 'contact'])
        warehouse = business and business.warehouse_id or False
        if not warehouse:
            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))
        sequence_obj = business.with_context(company_id=company.id).generate_sale_sequence()
        return {
            'name': sequence_obj.next_by_id(),
            'company_id': company.id,
            'fal_business_type': business.id,
            'warehouse_id': warehouse.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': self.date_order,
            'fiscal_position_id': partner.property_account_position_id.id,
            'payment_term_id': partner.property_payment_term_id.id,
            'user_id': False,
            'auto_generated': True,
            'partner_shipping_id': direct_delivery_address or partner_addr['delivery']
        }

    @api.model
    def _prepare_sale_order_line_data_business(self, line, business, company, sale_id):
        """ Generate the Sales Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param sale_id : the id of the SO
        """
        # it may not affected because of parallel company relation
        price = line.price_unit or 0.0
        taxes = line.taxes_id
        if line.product_id:
            taxes = line.product_id.taxes_id
        company_taxes = [tax_rec for tax_rec in taxes if tax_rec.company_id.id == company.id]
        if sale_id:
            so = self.env["sale.order"].with_user(business.interbusiness_user_id).browse(sale_id)
            company_taxes = so.fiscal_position_id.map_tax(company_taxes, line.product_id, so.partner_id)
        quantity = line.product_id and line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id) or line.product_qty
        price = line.product_id and line.product_uom._compute_price(price, line.product_id.uom_id) or price
        return {
            'name': line.name,
            'order_id': sale_id,
            'product_uom_qty': quantity,
            'product_id': line.product_id and line.product_id.id or False,
            'product_uom': line.product_id and line.product_id.uom_id.id or line.product_uom.id,
            'price_unit': price,
            'customer_lead': line.product_id and line.product_id.sale_delay or 0.0,
            'company_id': company.id,
            'tax_id': [(6, 0, company_taxes.ids)],
        }

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        picking_type_id = self.picking_type_id
        business = self.env['fal.business.type']._find_business_from_partner(self.partner_id.id)
        if self.fal_business_type and business and picking_type_id.code != 'internal':
            picking_type_id = self._get_default_internal_picking_type(self.fal_business_type.warehouse_id)
        if self.fal_business_type and picking_type_id.code == 'internal':
            res.update({
                'picking_type_id': picking_type_id.id,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
            })
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        picking_type_id = picking.picking_type_id
        if self.order_id.fal_business_type and picking_type_id.code == 'internal':
            for move in res:
                move.update({
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                })
        return res
