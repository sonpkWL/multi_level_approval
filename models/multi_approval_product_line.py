# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MultiApprovalProductLine(models.Model):
    _name = 'multi.approval.product.line'
    _description = 'Multi Product Line'
    _rec_name = 'product_id'
    _check_company_auto = True

    approval_request_id = fields.Many2one('multi.approval')
    approval_state = fields.Selection(related='approval_request_id.state')
    is_pic = fields.Boolean(compute='_check_pic', related='approval_request_id.is_pic')
    description = fields.Char(
        "Tên vật tư", required=True,
        compute="_compute_description", store=True, readonly=False, precompute=True)
    product_id = fields.Many2one('product.product', string="Mã vật tư", required=True)
    product_code = fields.Char(string='Mã VT', related='product_id.default_code', store=True)
    u_mawl = fields.Char(string='Mã WL', related='product_id.u_mawl', store=True)
    product_uom_id = fields.Many2one(
        'uom.uom', string="ĐVT",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True)
    uom = fields.Char(string='ĐVT')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    quantity = fields.Float("Số lượng", default=1.0)
    comment = fields.Char(string='Mục đích')
    yckt = fields.Char(string='Yêu cầu kĩ thuật')
    xuatxu = fields.Char(string='Xuất xứ')
    bpsd = fields.Many2one('hr.department', string='Bộ phận sử dụng', ondelete='cascade', select=True)
    state = fields.Selection(
        [('Approved', 'Phê duyệt'),
         ('Submitted', 'Chờ duyệt'),
         ('Refused', 'Từ chối')], default='Submitted', string='Trạng thái')
    user_sp_id = fields.Many2one('res.users', string='Người phụ trách')
    
    @api.depends('product_id')
    def _compute_description(self):
        for line in self:
            line.description = line.product_id.display_name

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id

    def action_approve_product(self):
        for item in self:
            item.write({
                'state': 'Approved'
            })
    def action_refuse_product(self):
        for item in self:
            item.write({
                'state': 'Refused'
            })
