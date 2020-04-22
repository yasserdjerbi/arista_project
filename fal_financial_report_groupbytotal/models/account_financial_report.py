# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import copy
import ast

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, ustr
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    def _get_columns_name_hierarchy(self, options):
        '''Calculates a hierarchy of column headers meant to be easily used in QWeb.

        This returns a list of lists. An example for 1 period and a
        filter that groups by company and partner:

        [
          [{'colspan': 2, 'name': 'As of 02/28/2018'}],
          [{'colspan': 2, 'name': 'YourCompany'}],
          [{'colspan': 1, 'name': 'ASUSTeK'}, {'colspan': 1, 'name': 'Agrolait'}],
        ]

        The algorithm used to generate this loops through each group
        id in options['groups'].get('ids') (group_ids). E.g. for
        group_ids:

        [(1, 8, 8),
         (1, 17, 9),
         (1, None, 9),
         (1, None, 13),
         (1, None, None)]

        These groups are always ordered. The algorithm loops through
        every first elements of each tuple, then every second element
        of each tuple etc. It generates a header element every time
        it:

        - notices a change compared to the last element (e.g. when processing 17
          it will create a dict for 8) or,
        - when a split in the row above happened

        '''
        if not options.get('groups', {}).get('ids'):
            return False

        periods = [{'string': self.format_date(options), 'class': 'number'}] + options['comparison']['periods']

        # generate specific groups for each period
        groups = []
        for period in periods:
            if len(periods) == 1 and self.debit_credit:
                for group in options['groups'].get('ids'):
                    groups.append(({'string': _('Debit'), 'class': 'number'},) + tuple(group))
                for group in options['groups'].get('ids'):
                    groups.append(({'string': _('Crebit'), 'class': 'number'},) + tuple(group))
            for group in options['groups'].get('ids'):
                groups.append((period,) + tuple(group))

        # add sentinel group that won't be rendered, this way we don't
        # need special code to handle the last group of every row
        groups.append(('sentinel',) * (len(options['groups'].get('fields', [])) + 1))

        column_hierarchy = []

        # row_splits ensures that we do not span over a split in the row above.
        # E.g. the following is *not* allowed (there should be 2 product sales):
        # | Agrolait | Camptocamp |
        # |  20000 Product Sales  |
        row_splits = []

        for field_index, field in enumerate(['period'] + options['groups'].get('fields')):
            current_colspan = 0
            current_group = False
            last_group = False

            # every report has an empty, unnamed header as the leftmost column
            current_hierarchy_line = [{'name': '', 'colspan': 1}]

            # We check if there is a change on date_from, means we are jumping year, means we need to have total (1)
            # CLuedoo Add-ons (1)
            last_date_from = False
            # End CLuedoo Add-ons
            for group_index, group_ids in enumerate(groups):
                # CLuedoo Add-ons (1)
                if 'date_from' in group_ids[0]:
                    current_date_from = group_ids[0]['date_from']
                else:
                    current_date_from = False
                # End CLuedoo Add-ons

                current_group = group_ids[field_index]
                if last_group is False:
                    last_group = current_group

                if last_group != current_group or group_index in row_splits:
                    current_hierarchy_line.append({
                        # field_index - 1 because ['period'] is not part of options['groups']['fields']
                        'name': last_group.get('string') if field == 'period' else self._get_column_name(last_group, options['groups']['fields'][field_index - 1]),
                        'colspan': current_colspan,
                        'class': 'number',
                    })
                    last_group = current_group
                    current_colspan = 0
                    row_splits.append(group_index)

                # CLuedoo Add-ons (1)
                if last_date_from != current_date_from:
                    if len(column_hierarchy) == 0:
                        current_hierarchy_line.append({'name': _('Total'), 'colspan': 1, 'class': 'number'})
                    else:
                        current_hierarchy_line.append({'name': '', 'colspan': 1, 'class': 'number'})
                    last_date_from = current_date_from
                # End CLuedoo Add-ons

                current_colspan += 1
            column_hierarchy.append(current_hierarchy_line)

        # CLuedoo Add-ons (1)
        if len(periods) == 1:
            for column_hierarchy_row in column_hierarchy:
                if column_hierarchy.index(column_hierarchy_row) == 0:
                    column_hierarchy_row.append({'name': _('Total'), 'colspan': 1, 'class': 'number'})
                else:
                    column_hierarchy_row.append({'name': '', 'colspan': 1, 'class': 'number'})
        # End CLuedoo Add-ons

        return column_hierarchy

    def _get_lines(self, options, line_id=None):
        line_obj = self.line_ids
        if line_id:
            line_obj = self.env['account.financial.html.report.line'].search([('id', '=', line_id)])
        if options.get('comparison') and options.get('comparison').get('periods'):
            line_obj = line_obj.with_context(periods=options['comparison']['periods'])
        if options.get('ir_filters'):
            line_obj = line_obj.with_context(periods=options.get('ir_filters'))

        currency_table = self._get_currency_table()
        domain, group_by = self._get_filter_info(options)

        if group_by:
            options['groups'] = {}
            options['groups']['fields'] = group_by
            options['groups']['ids'] = self._get_groups(domain, group_by)

        amount_of_periods = len((options.get('comparison') or {}).get('periods') or []) + 1
        # CLuedoo Changes
        if options.get('groups'):
            amount_of_group_ids = len(options.get('groups', {}).get('ids') or []) + 1 or 1
        else:
            amount_of_group_ids = len(options.get('groups', {}).get('ids') or []) or 1
        # CLuedoo
        linesDicts = [[{} for _ in range(0, amount_of_group_ids)] for _ in range(0, amount_of_periods)]

        res = line_obj.with_context(
            cash_basis=options.get('cash_basis'),
            filter_domain=domain,
        )._get_lines(self, currency_table, options, linesDicts)
        return res


class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    def _get_lines(self, financial_report, currency_table, options, linesDicts):
        final_result_table = []
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods', []) or []
        currency_precision = self.env.company.currency_id.rounding

        # build comparison table
        for line in self:
            res = []
            debit_credit = len(comparison_table) == 1
            domain_ids = {'line'}
            k = 0

            for period in comparison_table:
                date_from = period.get('date_from', False)
                date_to = period.get('date_to', False) or period.get('date', False)
                date_from, date_to, strict_range = line.with_context(date_from=date_from, date_to=date_to)._compute_date_range()

                r = line.with_context(date_from=date_from,
                                      date_to=date_to,
                                      strict_range=strict_range)._eval_formula(financial_report,
                                                                               debit_credit,
                                                                               currency_table,
                                                                               linesDicts[k],
                                                                               groups=options.get('groups'))
                # CLuedoo Addons
                if options.get('groups'):
                    per_line_total = {}
                    for column in r:
                        for row in column:
                            if row in per_line_total:
                                per_line_total[row]['balance'] += column[row]['balance']
                            else:
                                per_line_total[row] = {'balance': column[row]['balance']}
                    r.append(per_line_total)
                # End of CLuedoo Addons

                debit_credit = False
                res.extend(r)
                for column in r:
                    domain_ids.update(column)
                k += 1
            res = line._put_columns_together(res, domain_ids)

            if line.hide_if_zero and all([float_is_zero(k, precision_rounding=currency_precision) for k in res['line']]):
                continue

            # Post-processing ; creating line dictionnary, building comparison, computing total for extended, formatting
            vals = {
                'id': line.id,
                'name': line.name,
                'level': line.level,
                'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
                'columns': [{'name': l} for l in res['line']],
                'unfoldable': len(domain_ids) > 1 and line.show_domain != 'always',
                'unfolded': line.id in options.get('unfolded_lines', []) or line.show_domain == 'always',
                'page_break': line.print_on_new_page,
            }

            if financial_report.tax_report and line.domain and not line.action_id:
                vals['caret_options'] = 'tax.report.line'

            if line.action_id:
                vals['action_id'] = line.action_id.id
            domain_ids.remove('line')
            lines = [vals]
            groupby = line.groupby or 'aml'
            if line.id in options.get('unfolded_lines', []) or line.show_domain == 'always':
                if line.groupby:
                    domain_ids = sorted(list(domain_ids), key=lambda k: line._get_gb_name(k))
                for domain_id in domain_ids:
                    name = line._get_gb_name(domain_id)
                    if not self.env.context.get('print_mode') or not self.env.context.get('no_format'):
                        name = name[:40] + '...' if name and len(name) >= 45 else name
                    vals = {
                        'id': domain_id,
                        'name': name,
                        'level': line.level,
                        'parent_id': line.id,
                        'columns': [{'name': l} for l in res[domain_id]],
                        'caret_options': groupby == 'account_id' and 'account.account' or groupby,
                        'financial_group_line_id': line.id,
                    }
                    if line.financial_report_id.name == 'Aged Receivable':
                        vals['trust'] = self.env['res.partner'].browse([domain_id]).trust
                    lines.append(vals)
                if domain_ids and self.env.company.totals_below_sections:
                    lines.append({
                        'id': 'total_' + str(line.id),
                        'name': _('Total') + ' ' + line.name,
                        'level': line.level,
                        'class': 'o_account_reports_domain_total',
                        'parent_id': line.id,
                        'columns': copy.deepcopy(lines[0]['columns']),
                    })

            for vals in lines:
                if len(comparison_table) == 2 and not options.get('groups'):
                    vals['columns'].append(line._build_cmp(vals['columns'][0]['name'], vals['columns'][1]['name']))
                    for i in [0, 1]:
                        vals['columns'][i] = line._format(vals['columns'][i])
                else:
                    vals['columns'] = [line._format(v) for v in vals['columns']]
                if not line.formulas:
                    vals['columns'] = [{'name': ''} for k in vals['columns']]

            if len(lines) == 1:
                new_lines = line.children_ids._get_lines(financial_report, currency_table, options, linesDicts)
                if new_lines and line.formulas:
                    if self.env.company.totals_below_sections:
                        divided_lines = self._divide_line(lines[0])
                        result = [divided_lines[0]] + new_lines + [divided_lines[-1]]
                    else:
                        result = [lines[0]] + new_lines
                else:
                    if not new_lines and not lines[0]['unfoldable'] and line.hide_if_empty:
                        lines = []
                    result = lines + new_lines
            else:
                result = lines
            final_result_table += result

        return final_result_table
