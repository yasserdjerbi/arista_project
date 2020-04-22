# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FakturPajak(models.Model):
    _name = 'faktur.pajak'
    _description = 'Faktur Pajak Indonesia'

    kode_status_transkasi = fields.Char(
        string='kode Status Transaksi', size=3, compute='_get_status_code',
        readonly=True)
    tahun_penerbit = fields.Char(
        string='Tahun Penerbit', size=2,
        default=lambda self: fields.Date.from_string(
            fields.Date.context_today(self)
        ).strftime('%y'),
        states={'0': [('readonly', False)]},
        readonly=True
    )
    kode_cabang = fields.Char(
        string='Kode Cabang', size=3, default='000',
        states={'0': [('readonly', False)]},
        readonly=True)
    nomor_urut = fields.Char(
        string='Nomor Urut', size=8,
        states={'0': [('readonly', False)]},
        readonly=True)
    name = fields.Char(
        string='Nomor Faktur', compute='_get_faktur', store=True)
    invoice_id = fields.Many2one(
        'account.move', string='Invoice No.',
        states={'0': [('readonly', False)]},
        readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        states={'0': [('readonly', False)]},
        readonly=True)
    dpp = fields.Monetary(
        string='Untaxed Amount',
        states={'0': [('readonly', False)]},
        readonly=True)
    tax_amount = fields.Monetary(
        string='Tax Amount',
        states={'0': [('readonly', False)]},
        readonly=True)
    date_used = fields.Date(
        string='Used Date',
        states={'0': [('readonly', False)]},
        readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        states={'0': [('readonly', False)]},
        readonly=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        states={'0': [('readonly', False)]},
        readonly=True)
    faktur_pajak_ids = fields.One2many(
        'faktur.pajak.line', 'pajak_id', string='Faktur Pajak Line',
        states={'0': [('readonly', False)]},
        readonly=True)
    pajak_type = fields.Selection(
        [
            ('in', 'Faktur Pajak Masukan'),
            ('out', 'Faktur Pajak Keluaran')
        ], string='Type', default='out',
        states={'0': [('readonly', False)]},
        readonly=True
    )
    kode_transaksi = fields.Selection([
        ('01', '01 Kepada Pihak yang Bukan Pemungut PPN'),
        ('02', '02 Kepada Pemungut Bendaharawan'),
        ('03', '03 Kepada Pemungut Selain Bendaharawan'),
        ('04', '04 DPP Nilai Lain'),
        ('06', '06 Penyerahan Lainnya'),
        ('07', '07 Penyerahan yang PPN-nya Tidak Dipungut'),
        ('08', '08 Penyerahan yang PPN-nya Dibebaskan'),
        ('09', '09 Penyerahan Aktiva'),
    ], string='Kode Transaksi', default='01',
        states={'0': [('readonly', False)]},
        readonly=True)
    category = fields.Selection([
        ('0', 'Faktur Normal'),
        ('1', 'Faktur Pengganti'),
    ], string='Jenis Faktur', default='0',
        states={'0': [('readonly', False)]},
        readonly=True)
    state = fields.Selection(
        [
            ('0', 'Not Used'),
            ('1', 'Used'),
            ('2', 'Reported'),
            ('3', 'Cancelled')
        ], string='Status', default='0')

    @api.depends(
        'kode_transaksi',
        'category')
    def _get_status_code(self):
        for nomor in self:
            nomor.kode_status_transkasi = nomor.kode_transaksi + nomor.category

    @api.depends(
        'kode_status_transkasi',
        'kode_cabang', 'tahun_penerbit', 'nomor_urut')
    def _get_faktur(self):
        for nomor in self:
            name = '%s.%s-%s.%s' % (
                nomor.kode_status_transkasi,
                nomor.kode_cabang,
                nomor.tahun_penerbit, nomor.nomor_urut
            )
            nomor.name = name

    def used(self):
        faktur_line = self.env['faktur.pajak.line']
        for item in self:
            if item.faktur_pajak_ids:
                item.faktur_pajak_ids.unlink()
            if item.invoice_id:
                for x in item.invoice_id.invoice_line_ids:
                    line = {
                        'product_id': x.product_id.id,
                        'quantity': x.quantity,
                        'price_unit': x.price_unit,
                        'pajak_id': item.id,
                    }
                    faktur_line.create(line)
                item.write({'state': '1'})

    def report(self):
        self.write({'state': '2'})

    def cancel(self):
        self.write({'state': '3'})

    def set_to_draft(self):
        self.write({'state': '0'})

    _sql_constraints = [
        ('name_pajak_type_uniq', 'unique (name,pajak_type)',
            'Faktur pajak number already axist!')
    ]


class FakturPajakLine(models.Model):
    _name = 'faktur.pajak.line'
    _description = 'Faktur Pajak Line'

    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float('Quantity')
    price_unit = fields.Float(string="Price Unit")
    pajak_id = fields.Many2one('faktur.pajak', sting="Faktur Pajak")
