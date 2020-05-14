from odoo import fields, models, api, tools, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    fal_business_type_ids = fields.One2many('fal.business.type', 'company_id', string="Business Type")

    @api.model
    def create(self, vals):
        company = super(ResCompany, self).create(vals)
        # after creating new company
        # update non intra domain in IrFilter
        business_type = self.env['fal.business.type']
        business_type_ids = business_type.search([('company_id', '=', company.id)])
        if not business_type_ids and company:
            business_type.create({
                'name': _("Business Type A"),
                'company_id': company.id
                })
        return company
