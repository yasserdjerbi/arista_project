# -*- coding: utf-8 -*-
# Part of CLuedoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def webclient_rendering_context(self):
        """ Overrides community to prevent unnecessary load_menus request """
        return {
            'session_info': self.session_info(),
        }

    def session_info(self):
        user = request.env.user
        result = super(IrHttp, self).session_info()
        if self.env.user.has_group('base.group_user'):
            # Make a mapping of company and it's business type
            # So if user change business type, it should change company
            company_mapping = []
            for company, company_name in result['user_companies']['allowed_companies']:
                company_id = request.env['res.company'].browse(company)
                for business_type in company_id.fal_business_type_ids.filtered(lambda x: x.id in user.fal_allowed_business_type_ids.ids):
                    company_mapping.append((company_id.id, business_type.id))
            result.update({
                "user_business_types": {'current_business_type': (user.fal_business_type_id.id, user.fal_business_type_id.name), 'business_types': [(bts.id, bts.name) for bts in user.fal_business_type_ids], 'allowed_business_types': [(bts.id, bts.name) for bts in user.fal_allowed_business_type_ids]},
                "display_switch_business_types_menu": len(user.fal_business_type_ids) > 0,
                "company_business_type_map": company_mapping,
            })
        return result
