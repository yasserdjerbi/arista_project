# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class BusinessType(models.Model):
    _inherit = 'fal.business.type'

    internal_transit_location_id = fields.Many2one(
        'stock.location', 'Internal Transit Location', ondelete="restrict",
        help="Technical field used for resupply routes between warehouses that belong to this business types")

    def _create_transit_location(self):
        '''Create a transit location with fal_business_type being the given fal_business_type. This is needed
           in case of resuply routes between warehouses belonging to the same fal_business_type, because
           we don't want to create accounting entries at that time.
        '''
        parent_location = self.env.ref('stock.stock_location_locations', raise_if_not_found=False)
        for bt in self:
            location = self.env['stock.location'].create({
                'name': _('%s: Transit Location') % bt.name,
                'usage': 'transit',
                'location_id': parent_location and parent_location.id or False,
                'company_id': bt.company_id.id,
                'fal_business_type': bt.id,
            })
            bt.write({'internal_transit_location_id': location.id})

            bt.partner_id.with_context(force_business_type=bt.id, force_company=bt.company_id.id).write({
                'property_stock_customer': location.id,
                'property_stock_supplier': location.id,
            })

    def _create_inventory_loss_location(self):
        parent_location = self.env.ref('stock.stock_location_locations_virtual', raise_if_not_found=False)
        inventory_loss_product_template_field = self.env['ir.model.fields'].search([('model','=','product.template'),('name','=','property_stock_inventory')])
        for bt in self:
            inventory_loss_location = self.env['stock.location'].create({
                'name': '%s: Inventory adjustment' % bt.name,
                'usage': 'inventory',
                'location_id': parent_location.id,
                'company_id': bt.company_id.id,
                'fal_business_type': bt.id,
            })
            self.env['ir.property'].create({
                'name': 'property_stock_inventory_%s' % bt.name,
                'fields_id': inventory_loss_product_template_field.id,
                'company_id': bt.company_id.id,
                'fal_business_type': bt.id,
                'value': 'stock.location,%d' % inventory_loss_location.id,
            })

    def _create_production_location(self):
        parent_location = self.env.ref('stock.stock_location_locations_virtual', raise_if_not_found=False)
        production_product_template_field = self.env['ir.model.fields'].search([('model','=','product.template'),('name','=','property_stock_production')])
        for bt in self:
            production_location = self.env['stock.location'].create({
                'name': '%s: Production' % bt.name,
                'usage': 'production',
                'location_id': parent_location.id,
                'company_id': bt.company_id.id,
                'fal_business_type': bt.id,
            })
            self.env['ir.property'].create({
                'name': 'property_stock_inventory_%s' % bt.name,
                'fields_id': production_product_template_field.id,
                'company_id': bt.company_id.id,
                'fal_business_type': bt.id,
                'value': 'stock.location,%d' % production_location.id,
            })

    def _create_scrap_location(self):
        for bt in self:
            parent_location = self.env.ref('stock.stock_location_locations_virtual', raise_if_not_found=False)
            scrap_location = self.env['stock.location'].create({
                'name': '%s: Scrap' % bt.name,
                'usage': 'inventory',
                'location_id': parent_location.id,
                'company_id': bt.company_id.id,
                'fal_business_type': bt.id,
                'scrap_location': True,
            })

    def _create_scrap_sequence(self):
        scrap_vals = []
        for bt in self:
            scrap_vals.append({
                'name': '%s Sequence scrap' % bt.name,
                'code': 'stock.scrap',
                'company_id': bt.company_id.id,
                'fal_business_type': bt.id,
                'prefix': 'SP/',
                'padding': 5,
                'number_next': 1,
                'number_increment': 1
            })
        if scrap_vals:
            self.env['ir.sequence'].create(scrap_vals)

    @api.model
    def create_missing_warehouse(self):
        """ This hook is used to add a warehouse on existing companies
        when module stock is installed.
        """
        business_type_ids = self.env['fal.business.type'].search([])
        business_type_with_warehouse = self.env['stock.warehouse'].search([]).mapped('fal_business_type')
        business_type_without_warehouse = business_type_ids - business_type_with_warehouse
        for business_type in business_type_without_warehouse:
            self.env['stock.warehouse'].create({
                'name': business_type.name,
                'code': business_type.name[:5],
                'company_id': business_type.company_id.id,
                'fal_business_type': business_type.id,
                'partner_id': business_type.partner_id.id,
            })

    @api.model
    def create_missing_transit_location(self):
        business_type_without_transit = self.env['fal.business.type'].search([('internal_transit_location_id', '=', False)])
        for business_type in business_type_without_transit:
            business_type._create_transit_location()

    @api.model
    def create_missing_inventory_loss_location(self):
        business_type_ids = self.env['fal.business.type'].search([])
        inventory_loss_product_template_field = self.env['ir.model.fields'].search([('model','=','product.template'),('name','=','property_stock_inventory')])
        business_types_having_property = self.env['ir.property'].search([('fields_id', '=', inventory_loss_product_template_field.id)]).mapped('fal_business_type')
        business_type_without_property = business_type_ids - business_types_having_property
        for business_type in business_type_without_property:
            business_type._create_inventory_loss_location()

    @api.model
    def create_missing_production_location(self):
        business_type_ids = self.env['fal.business.type'].search([])
        production_product_template_field = self.env['ir.model.fields'].search([('model','=','product.template'),('name','=','property_stock_production')])
        business_types_having_property = self.env['ir.property'].search([('fields_id', '=', production_product_template_field.id)]).mapped('fal_business_type')
        business_type_without_property = business_type_ids - business_types_having_property
        for business_type in business_type_without_property:
            business_type._create_production_location()

    @api.model
    def create_missing_scrap_location(self):
        business_type_ids = self.env['fal.business.type'].search([])
        business_types_having_scrap_loc = self.env['stock.location'].search([('scrap_location', '=', True)]).mapped('fal_business_type')
        business_type_without_property = business_type_ids - business_types_having_scrap_loc
        for business_type in business_type_without_property:
            business_type._create_scrap_location()

    @api.model
    def create_missing_scrap_sequence(self):
        business_type_ids = self.env['fal.business.type'].search([])
        business_type_has_scrap_seq = self.env['ir.sequence'].search([('code', '=', 'stock.scrap')]).mapped('fal_business_type')
        business_type_todo_sequence = business_type_ids - business_type_has_scrap_seq
        business_type_todo_sequence._create_scrap_sequence()

    def _create_per_bt_locations(self):
        self.ensure_one()
        self._create_transit_location()
        self._create_inventory_loss_location()
        self._create_production_location()
        self._create_scrap_location()

    def _create_per_bt_sequences(self):
        self.ensure_one()
        self._create_scrap_sequence()

    def _create_per_bt_picking_types(self):
        self.ensure_one()

    def _create_per_bt_rules(self):
        self.ensure_one()

    @api.model
    def create(self, vals):
        bt = super(BusinessType, self).create(vals)
        bt.sudo()._create_per_bt_locations()
        bt.sudo()._create_per_bt_sequences()
        bt.sudo()._create_per_bt_picking_types()
        bt.sudo()._create_per_bt_rules()
        self.env['stock.warehouse'].sudo().create({'name': bt.name, 'code': bt.name[:5], 'company_id': bt.company_id.id, 'fal_business_type': bt.id, 'partner_id': bt.partner_id.id})
        return bt
