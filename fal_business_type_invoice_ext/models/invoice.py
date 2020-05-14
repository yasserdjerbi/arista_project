from odoo import fields, models, api, tools, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # ########################################
    # Default Function
    # We need to override this, to include business type in journal search
    @api.model
    def _get_default_journal(self):
        move_type = self._context.get('default_type', 'entry')
        journal_type = 'general'
        if move_type in self.get_sale_types(include_receipts=True):
            journal_type = 'sale'
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_type = 'purchase'

        if self._context.get('default_journal_id'):
            journal = self.env['account.journal'].browse(self._context['default_journal_id'])

            if move_type != 'entry' and journal.type != journal_type:
                raise UserError(_("Cannot create an invoice of type %s with a journal having %s as type.") % (move_type, journal.type))
        else:
            company_id = self._context.get('force_company', self._context.get('default_company_id', self.env.company.id))
            domain = [('company_id', '=', company_id), ('type', '=', journal_type)]

            # Change Start Here
            if self.env.user.fal_business_type_id:
                domain = domain + [('fal_business_type', '=', self.env.user.fal_business_type_id.id)]
            # Change End Here

            journal = None
            if self._context.get('default_currency_id'):
                currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
                journal = self.env['account.journal'].search(currency_domain, limit=1)

            if not journal:
                journal = self.env['account.journal'].search(domain, limit=1)

            if not journal:
                error_msg = _('Please define an accounting miscellaneous journal in your company / business type')
                if journal_type == 'sale':
                    error_msg = _('Please define an accounting sale journal in your company / business type')
                elif journal_type == 'purchase':
                    error_msg = _('Please define an accounting purchase journal in your company / business type')
                raise UserError(error_msg)
        return journal

    # ########################################
    # Fields Definition
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", store=True, readonly=True, related='journal_id.fal_business_type', change_default=True)
    # Redefine this field to take new default function
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('company_id', '=', company_id)]",
        default=_get_default_journal)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for move in self:
            if move.fal_business_type.company_id and move.company_id:
                if move.fal_business_type.company_id != move.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", related="move_id.fal_business_type", store=True)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    fal_business_type = fields.Many2one("fal.business.type", required=True, index=True, string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default, help="Business Type related to this journal")

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for journal in self:
            if journal.fal_business_type.company_id and journal.company_id:
                if journal.fal_business_type.company_id != journal.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountJournalGroup(models.Model):
    _inherit = "account.journal.group"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # I do not know yet about the required
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for journal in self:
            if journal.fal_business_type.company_id and journal.company_id:
                if journal.fal_business_type.company_id != journal.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountAccount(models.Model):
    _inherit = "account.account"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for account in self:
            if account.fal_business_type.company_id and account.company_id:
                if account.fal_business_type.company_id != account.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for account in self:
            if account.fal_business_type.company_id and account.company_id:
                if account.fal_business_type.company_id != account.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountFiscal(models.Model):
    _inherit = "account.fiscal.position"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for account in self:
            if account.fal_business_type.company_id and account.company_id:
                if account.fal_business_type.company_id != account.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for account in self:
            if account.fal_business_type.company_id and account.company_id:
                if account.fal_business_type.company_id != account.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", related="statement_id.fal_business_type", store=True)


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for account in self:
            if account.fal_business_type.company_id and account.company_id:
                if account.fal_business_type.company_id != account.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for account in self:
            if account.fal_business_type.company_id and account.company_id:
                if account.fal_business_type.company_id != account.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]", default=_get_business_type_default)

    @api.constrains('fal_business_type', 'company_id')
    def _check_business_type(self):
        for account in self:
            if account.fal_business_type.company_id and account.company_id:
                if account.fal_business_type.company_id != account.company_id:
                    raise AccessError(_('You cannot select business unit from different company'))


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    def _get_business_type_default(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return user_id.fal_business_type_id or False

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", readonly=True, default=_get_business_type_default)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ',move.fal_business_type AS fal_business_type'

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ',move.fal_business_type'


class AccountRoot(models.Model):
    _inherit = 'account.root'

    # No required here because it maybe not related to a company
    fal_business_type = fields.Many2one("fal.business.type")

    #  override method
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT DISTINCT ASCII(code) * 1000 + ASCII(SUBSTRING(code,2,1)) AS id,
                   LEFT(code,2) AS name,
                   ASCII(code) AS parent_id,
                   company_id,
                   fal_business_type
            FROM account_account WHERE code IS NOT NULL
            UNION ALL
            SELECT DISTINCT ASCII(code) AS id,
                   LEFT(code,1) AS name,
                   NULL::int AS parent_id,
                   company_id,
                   fal_business_type
            FROM account_account WHERE code IS NOT NULL
            )''' % (self._table,)
        )
