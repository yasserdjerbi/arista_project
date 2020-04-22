from odoo import models, fields, api
import base64
import csv


class FalAccountInvoice(models.TransientModel):
    _name = 'fal.account.invoice'
    _description = 'Export E-Faktur'

    fal_file_content = fields.Binary(copy=False)
    filename = fields.Char(copy=False)

    def export_efaktur(self):
        # Data Tax
        cek_invoices = self.env['account.move'].browse(
            self._context.get('active_ids', []))
        if cek_invoices:
            first_inv = cek_invoices[0]
            customer = ["out_invoice", "out_refund"]
            if first_inv.type in customer:
                # Header Tax
                myData = [
                    [
                        'FK',
                        'KD_JENIS_TRANSAKSI',
                        'FG_PENGGANTI',
                        'NOMOR_FAKTUR',
                        'MASA_PAJAK',
                        'TAHUN_PAJAK',
                        'TANGGAL_FAKTUR',
                        'NPWP',
                        'NAMA',
                        'ALAMAT_LENGKAP',
                        'JUMLAH_DPP',
                        'JUMLAH_PPN',
                        'JUMLAH_PPNBM',
                        'ID_KETERANGAN_TAMBAHAN',
                        'FG_UANG_MUKA',
                        'UANG_MUKA_DPP',
                        'UANG_MUKA_PPN',
                        'UANG_MUKA_PPNBM',
                        'REFERENSI',
                    ]
                ]
                myData += [
                    [
                        'LT',
                        'NPWP',
                        'NAMA',
                        'JALAN',
                        'BLOK',
                        'NOMOR',
                        'RT',
                        'RW',
                        'KECAMATAN',
                        'KELURAHAN',
                        'KABUPATEN',
                        'PROPINSI',
                        'KODE_POS',
                        'NOMOR_TELEPON',
                    ]
                ]
                myData += [
                    [
                        'OF',
                        'KODE_OBJEK',
                        'NAMA',
                        'HARGA_SATUAN',
                        'JUMLAH_BARANG',
                        'HARGA_TOTAL',
                        'DISKON',
                        'DPP',
                        'PPN',
                        'TARIF_PPNBM',
                        'PPNBM',
                    ]
                ]

                invoices = self.env['account.move'].browse(
                    self._context.get('active_ids', []))
                for order in invoices:
                    amount_untaxed = 0
                    amount_tax = 0
                    for line in order.invoice_line_ids:
                        taxes = line.tax_ids.compute_all(line.price_unit, line.move_id.currency_id, line.quantity, line.product_id, line.move_id.partner_id)
                        amount_untaxed += int(line.price_subtotal)
                        amount_tax += int(taxes['taxes'][0]['amount']) if taxes['taxes'] else '0'

                    myData += [
                        [
                            'FK',
                            order.faktur_pajak_id.kode_transaksi,
                            order.faktur_pajak_id.category,
                            str(order.faktur_pajak_id.kode_cabang) +
                            str(order.faktur_pajak_id.tahun_penerbit) +
                            str(order.faktur_pajak_id.nomor_urut),
                            int(order.invoice_date and order.invoice_date.strftime('%m')),
                            order.invoice_date and order.invoice_date.strftime('%Y'),
                            order.invoice_date and order.invoice_date.strftime('%d/%m/%Y'),
                            order.npwp,
                            order.partner_id.name,
                            order.partner_id.street,
                            amount_untaxed,
                            amount_tax,
                            '0',
                            '',
                            '0',
                            '0',
                            '0',
                            '0',
                            order.name or order.origin or '',
                        ]
                    ]

                    for line in order.invoice_line_ids:
                        taxes = line.tax_ids.compute_all(line.price_unit, line.move_id.currency_id, line.quantity, line.product_id, line.move_id.partner_id)
                        myData += [
                            [
                                'OF',
                                line.product_id.default_code or '',
                                line.product_id.name or '',
                                int(line.price_unit),
                                line.quantity,
                                int(line.price_subtotal),
                                (line.quantity * (
                                    line.price_unit * (line.discount / 100))) +
                                0.0,
                                int(line.price_subtotal),
                                int(taxes['taxes'][0]['amount']) if taxes['taxes'] else '0',
                                '0',
                                '0',
                            ]
                        ]

                    myFile = open('/tmp/efaktur_out.csv', 'w')
                    with myFile:
                        writer = csv.writer(
                            myFile, delimiter=',',
                            lineterminator='\r\n',
                            quotechar='"',
                            quoting=csv.QUOTE_ALL
                        )
                        writer.writerows(myData)

                    f = open('/tmp/efaktur_out.csv', 'r')

                    file = f.read()
                    self.fal_file_content = base64.b64encode(file.encode('utf-8'))
                    self.filename = 'efaktur_out.csv'
                    f.close()
            else:
                # Header Tax
                myData = [
                    [
                        "FM",
                        "KD_JENIS_TRANSAKSI",
                        "FG_PENGGANTI",
                        "NOMOR_FAKTUR",
                        "MASA_PAJAK",
                        "TAHUN_PAJAK",
                        "TANGGAL_FAKTUR",
                        "NPWP",
                        "NAMA",
                        "ALAMAT_LENGKAP",
                        "JUMLAH_DPP",
                        "JUMLAH_PPN",
                        "JUMLAH_PPNBM",
                        "IS_CREDITABLE"
                    ]
                ]
                invoices = self.env['account.move'].browse(
                    self._context.get('active_ids', []))
                for order in invoices:
                    nfp = order.nomor_faktur_pajak
                    fp = nfp if nfp else '0000000000000000'
                    npwp = order.npwp if nfp else '0000000000000000'
                    myData += [
                        [
                            'FM',
                            order.faktur_pajak_id.kode_transaksi,
                            order.faktur_pajak_id.category,
                            str(fp[-13:]),
                            int(order.invoice_date.strftime('%m')),
                            order.invoice_date.strftime('%Y'),
                            order.invoice_date.strftime('%d/%m/%Y'),
                            str(npwp),
                            order.partner_id.name,
                            order.partner_id.street,
                            int(order.amount_untaxed),
                            int(order.amount_tax),
                            '0',
                            '1',
                        ]
                    ]
                myFile = open('/tmp/efaktur_in.csv', 'w')
                with myFile:
                    writer = csv.writer(
                        myFile, delimiter=',',
                        lineterminator='\r\n',
                        quotechar='"',
                        quoting=csv.QUOTE_ALL
                    )
                    writer.writerows(myData)

                f = open('/tmp/efaktur_in.csv', 'r')

                file = f.read()
                self.fal_file_content = base64.b64encode(file.encode('utf-8'))
                self.filename = 'efaktur_in.csv'
                f.close()

            return {
                'name': 'E-Faktur',
                'type': 'ir.actions.act_url',
                'url': "web/content/?model=fal.account.invoice&id=" + str(self.id) + "&filename_field=filename&field=fal_file_content&download=true&filename=" + self.filename,
                'target': 'self',
            }
