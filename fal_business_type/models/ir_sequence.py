from odoo import fields, models, api, tools, _


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type or False

    fal_business_type = fields.Many2one('fal.business.type', string="Business Type", default=_get_business_type_default, domain="[('company_id', '=', company_id)]")

    @api.model
    def next_by_code(self, sequence_code, sequence_date=None):
        """ Need to override here
        """
        self.check_access_rights('read')
        force_company = self._context.get('force_company')
        if not force_company:
            force_company = self.env.company.id
        force_business_type = self._context.get('force_business_type')
        if not force_business_type:
            user_id = self.env['res.users'].browse(self.env.uid)
            force_business_type = user_id.fal_business_type or False
        seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [force_company, False]), ('fal_business_type', 'in', [force_business_type, False])], order='company_id')
        if not seq_ids:
            _logger.debug("No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current company." % sequence_code)
            return False
        seq_id = seq_ids[0]
        return seq_id._next(sequence_date=sequence_date)
