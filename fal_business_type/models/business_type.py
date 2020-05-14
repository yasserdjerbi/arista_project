from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class BusinessType(models.Model):
    _name = 'fal.business.type'
    _description = 'Cluedoo business type'

    name = fields.Char(
        'Name', copy=False, default='New', required=True
    )
    company_id = fields.Many2one('res.company', string="Company", required=True, index=True, default=lambda self: self.env.company, ondelete='cascade')
    fal_business_prefix = fields.Char(
        'Default Prefix', copy=False
    )
    fal_business_suffix = fields.Char(
        'Default Suffix', copy=False
    )
    active = fields.Boolean(default=True, help="The active field allows you to hide the category without removing it.")
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)

    def launch_create_menu_wizard(self):
        view_id = self.env.ref('fal_business_type.business_create_menu_wizard_form_view').id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Menu'),
            'view_mode': 'form',
            'res_model': 'create.menu.wizard',
            'target': 'new',
            'views': [[view_id, 'form']],
            'context': {'active_id': self.id, 'default_name': self.name},
        }

    @api.model
    def create(self, vals):
        partner = self.env['res.partner'].create({
            'name': vals['name'],
            'is_business_partner': True,
        })
        vals['partner_id'] = partner.id
        return super(BusinessType, self).create(vals)
