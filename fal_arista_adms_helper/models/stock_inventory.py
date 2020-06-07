# -*- coding: utf-8 -*-
from odoo import models, api
from lxml.builder import E


class Inventory(models.AbstractModel):
    _inherit = 'stock.inventory'

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def adms_import(self, list_vals):
        model = self.env['ir.model'].search([('model', '=', self._name)], limit=1)
        for vals in list_vals:
            # 1. Translate any adms_id field into standard field
            new_vals = self.iterate_and_compute(model, vals)
            # 2. Determine wether it's create new or write
            similar_adms_id = self.search([('x_studio_adms_id', '=', vals['x_studio_adms_id'])])
            if similar_adms_id:
                result = similar_adms_id.write(new_vals)
                return similar_adms_id
            else:
                result = self.create(new_vals)
                return result
        return "Something Went Wrong"

    def iterate_and_compute(self, model, vals):
        new_vals = {}
        # For every field in vals
        for key in vals:
            # If it's list. It can means 2 possibilities
            if isinstance(vals[key], list):
                # Need to change the model to the list field model
                field = self.env['ir.model.fields'].search([('model_id', '=', model.id), ('name', '=', key)])
                model = self.env['ir.model'].search([('model', '=', field.relation)], limit=1)
                for o2m in vals[key]:
                    # If it's 0, Means we need to define if it's creating new object or just
                    # editing it by checking the adms id
                    # If it's 6, Means we only relate the id, and so just need to find out the
                    # real id
                    if o2m[0] == 0:
                        res = self.iterate_and_compute(model, o2m[2])
                        # If there is adms id, and adms id is already available,
                        # means we just need to edit available adms ID
                        if 'x_studio_adms_id' in o2m[2] and self.env[model.model].search([('x_studio_adms_id', '=', o2m[2]['x_studio_adms_id'])]):
                            new_vals[key] = [(1, self.env[model.model].search([('x_studio_adms_id', '=', o2m[2]['x_studio_adms_id'])]).ids, res)]
                        else:
                            new_vals[key] = [(0, 0, res)]
                    elif o2m[0] == 6:
                        new_o2mid = []
                        for o2mid in o2m[2]:
                            new_o2mid.append(self.env[model.model].search([('x_studio_adms_id', '=', o2mid)], limit=1).id)
                        new_vals[key] = [(6, 0, new_o2mid)]
            # If it's a share id field for many2one relation
            # Find the object based on field search
            elif "x_studio_adms_id_" in key:
                # We try to get the real field name
                # It's always the 18th word
                field_name = key[17:]
                field = self.env['ir.model.fields'].search([('model_id', '=', model.id), ('name', '=', field_name)])
                real_id = self.env[field.relation].search([('x_studio_adms_id', '=', vals[key])], limit=1)
                new_vals[key[17:]] = real_id.id
                new_vals[key] = vals[key]
                if key == 'x_studio_adms_id_fal_business_type':
                    new_vals['company_id'] = real_id.company_id.id
            # If it's auto locate means we need to define it's new value location
            elif 'auto_locate' in key:
                if 'location_id' not in new_vals:
                    warehouse = self.env['stock.warehouse'].search([('company_id', '=', new_vals['company_id']), ('fal_business_type', '=', new_vals['fal_business_type'])], limit=1)
                    if warehouse:
                        new_vals['location_id'] = warehouse.lot_stock_id.id
            # Other field we just copy-paste
            else:
                new_vals[key] = vals[key]
        return new_vals


class InventoryLine(models.AbstractModel):
    _inherit = 'stock.inventory.line'

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def adms_import(self, list_vals):
        model = self.env['ir.model'].search([('model', '=', self._name)], limit=1)
        for vals in list_vals:
            # 1. Translate any adms_id field into standard field
            new_vals = self.iterate_and_compute(model, vals)
            # 2. Determine wether it's create new or write
            similar_adms_id = self.search([('x_studio_adms_id', '=', vals['x_studio_adms_id'])])
            if similar_adms_id:
                result = similar_adms_id.write(new_vals)
                return similar_adms_id
            else:
                result = self.create(new_vals)
                return result
        return "Something Went Wrong"

    def iterate_and_compute(self, model, vals):
        new_vals = {}
        # For every field in vals
        for key in vals:
            # If it's list. It can means 2 possibilities
            if isinstance(vals[key], list):
                # Need to change the model to the list field model
                field = self.env['ir.model.fields'].search([('model_id', '=', model.id), ('name', '=', key)])
                model = self.env['ir.model'].search([('model', '=', field.relation)], limit=1)
                for o2m in vals[key]:
                    # If it's 0, Means we need to define if it's creating new object or just
                    # editing it by checking the adms id
                    # If it's 6, Means we only relate the id, and so just need to find out the
                    # real id
                    if o2m[0] == 0:
                        res = self.iterate_and_compute(model, o2m[2])
                        # If there is adms id, and adms id is already available,
                        # means we just need to edit available adms ID
                        if 'x_studio_adms_id' in o2m[2] and self.env[model.model].search([('x_studio_adms_id', '=', o2m[2]['x_studio_adms_id'])]):
                            new_vals[key] = [(1, self.env[model.model].search([('x_studio_adms_id', '=', o2m[2]['x_studio_adms_id'])]).ids, res)]
                        else:
                            new_vals[key] = [(0, 0, res)]
                    elif o2m[0] == 6:
                        new_o2mid = []
                        for o2mid in o2m[2]:
                            new_o2mid.append(self.env[model.model].search([('x_studio_adms_id', '=', o2mid)], limit=1).id)
                        new_vals[key] = [(6, 0, new_o2mid)]
            # If it's a share id field for many2one relation
            # Find the object based on field search
            elif "x_studio_adms_id_" in key:
                # We try to get the real field name
                # It's always the 18th word
                field_name = key[17:]
                field = self.env['ir.model.fields'].search([('model_id', '=', model.id), ('name', '=', field_name)])
                real_id = self.env[field.relation].search([('x_studio_adms_id', '=', vals[key])], limit=1)
                new_vals[key[17:]] = real_id.id
                new_vals[key] = vals[key]
                if key == 'x_studio_adms_id_fal_business_type':
                    new_vals['company_id'] = real_id.company_id.id
            # If it's auto locate means we need to define it's new value location
            elif 'auto_locate' in key:
                if 'location_id' not in new_vals:
                    company_id = self.env['fal.business.type'].browse(new_vals['fal_business_type']).company_id
                    warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id.id), ('fal_business_type', '=', new_vals['fal_business_type'])], limit=1)
                    if warehouse:
                        new_vals['location_id'] = warehouse.lot_stock_id.id
            # Other field we just copy-paste
            else:
                new_vals[key] = vals[key]
        return new_vals
