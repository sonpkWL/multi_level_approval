# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright Domiup (<http://domiup.com>).
#
##############################################################################

import math
from dateutil.relativedelta import relativedelta
from random import randint

from odoo import api, models, fields , tools, Command, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_resource
import logging
from collections import defaultdict
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.addons.iap.tools import iap_tools
from odoo.addons.web.controllers.utils import clean_action

_logger = logging.getLogger(__name__)

def change_time_off(self):
    view_id = self.env.ref(
            'hr_leave_views.hr_leave_view_dashboard', False)
    return {
        'name':_('New Request'),
        'view_mode':'calendar',
        'res_model':'hr.leave',
        'view_id': view_id and view_id.id or False,
        'type': 'ir.actions.act_window',
        'context': {
            'default_type_id': self.id,
        }
    }
def change_time_off_approval(self):
    view_id = self.env.ref(
            'hr_leave_views.hr_leave_view_calendar', False)
    return {
        'name':_('New Request'),
        'view_mode':'calendar',
        'res_model':'hr.leave',
        'view_id': view_id and view_id.id or False,
        'type': 'ir.actions.act_window',
        'context': {
            'default_type_id': self.id,
        }
    }


class MultiApprovalType(models.Model):
    _name = 'multi.approval.type'
    _description = 'Multi Approval Type'

    name = fields.Char(string='Name', required=True)
    description = fields.Char(string='Description')
    image = fields.Binary(attachment=True)
    active = fields.Boolean(string='Active', default=True, readonly=False)
    # company_id = fields.Many2one(
    #     'res.company', 'Company', copy=False,
    #     required=True, index=True, default=lambda s: s.env.company)
    mail_notification = fields.Boolean()
    mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Template for the request",
        help="Let it empty if you want to send the description of the request"
    )
    approve_mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Template of `Approved` Case",
        help="Let it empty if don't want notify"
    )
    refuse_mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Template of `Refused` Case",
        help="Let it empty if don't want notify"
    )
    user_ids = fields.Many2many('res.users', compute='_compute_user_ids', string="Approver Users")
    approv_ids = fields.One2many(
        'multi.approval.type.line.noti', 'approv_id', string="Approv",
        required=True)
    user_xuong_ids = fields.Many2many('res.users', compute='_compute_user_xuong_ids', string="Approver Users")
    xuong_ids = fields.One2many(
        'multi.approval.type.line.xuong', 'type_id', string="Approve Xuong",
        required=True)
    user_line_ids = fields.Many2many('res.users', compute='_compute_user_line_ids', string="Approver Users")
    line_ids = fields.One2many(
        'multi.approval.type.line', 'type_id', string="Approvers",
        required=True)
    approval_minimum = fields.Integer(
        string='Minimum Approvers', compute='_get_approval_minimum',
        readonly=True)
    approv_minimum = fields.Integer(
        string='Minimum Approvers', compute='_get_approv_minimum',
        readonly=True)
    xuong_minimum = fields.Integer(
        string='Minimum Approvers', compute='_get_xuong_minimum',
        readonly=True)
    manager_approval = fields.Selection([('Optional', 'Is Approver'), ('Required', 'Is Required Approver')],
                                        string="Employee's Manager",
                                        help="""How the employee's manager interacts with this type of approval.

            Empty: do nothing
            Is Approver: the employee's manager will be in the approver list
            Is Required Approver: the employee's manager will be required to approve the request.
        """)
    manager_stt = fields.Integer(string=' STT người quản lý')
    manager_name = fields.Char(string='Tiêu đề người quản lý')
    warehouse_approval = fields.Selection([('Optional', 'Nhận thông tin'), ('Required', 'Phê duyệt')]
                                          , string="Người quản lý kho")
    warehouse_stt = fields.Integer(string=' STT người quản lý kho')
    warehouse_name = fields.Char(string='Tiêu đề người quản lý kho')
    quanly_approval = fields.Selection([('Optional', 'Nhận thông tin'), ('Required', 'Phê duyệt')]
                                          , string="Người quản lý cấp 2")
    quanly_stt = fields.Integer(string=' STT người quản lý cấp 2')
    quanly_name = fields.Char(string='Tiêu đề người quản lý cấp 2')
    # employee_ids = fields.Many2many('hr.employee', string='Nhân viên')
    document_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ], string="Document", default='Optional')
    contact_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Contact", default='None')
    date_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Date", default='None')
    period_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Period", default='None')
    item_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Item", default='None')
    multi_items_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Multi Items", default='None')

    quantity_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Quantity", default='None')
    amount_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Amount", default='None')
    reference_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Reference", default='None')
    payment_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Payment", default='None')
    location_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Location", default='None')
    tt_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="TT Item", default='None')
    reason_wl_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Lý do", default='None')
    warehouse_wl_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Kho", default='None')
    nhamay_wl_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Nhà máy", default='None')
    nhamaywl_opt = fields.Many2one('hr.nhamay.wl', string='Nhà máy')
    # item_line_ids = fields.One2many(
    #     'multi.approval.item.line', 'type_id', string="TT Items",
    #     required=True)
    submitted_nb = fields.Integer(
        string="To Review",
        compute="_get_submitted_request")
    activity_notification = fields.Boolean()
    domain_type = fields.Text(string='Domain')
    product_category_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Nhóm hàng hóa", default='None')
    NM_opt = fields.Boolean(string="Bảo vệ theo NM")
    type_approval = fields.Boolean(string="Áp dụng ĐK phê duyệt")
    ticket_properties = fields.PropertiesDefinition('Ticket Properties')
    user_xuong_opt = fields.Boolean(string="ĐK theo Xưởng")
    xuong_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ('None', 'None'),
         ], string="Xưởng", default='None')
    # security_user_type_id = fields.Boolean(string="Phân quyền user")
    # properties = fields.Properties(
    #     'Properties', definition='ticket_properties',
    #     copy=True)

    def _get_submitted_request(self):
        for r in self:
            r.submitted_nb = self.env['multi.approval'].search_count(
                [('type_id', '=', r.id), ('state', '=', 'Submitted')])

    # @api.depends('uid')
    # def _get_security_type(self):
    #     user = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1).multi_approval_type_ids
    #     for r in self:
    #         r.security_user_type_id = False
    #         if r.id in user:
    #             r.security_user_type_id = True

    @api.depends('line_ids')
    def _get_approval_minimum(self):
        for rec in self:
            required_lines = rec.line_ids.filtered(
                lambda l: l.require_opt == 'Required')
            rec.approval_minimum = len(required_lines)

    @api.depends('approv_ids')
    def _get_approv_minimum(self):
        for rec in self:
            optional_lines = rec.approv_ids.filtered(
                lambda l: l.require_opt == 'Optional')
            rec.approv_minimum = len(optional_lines)

    @api.depends('xuong_ids')
    def _get_xuong_minimum(self):
        for rec in self:
            optional_lines = rec.xuong_ids.filtered(
                lambda l: l.require_opt == 'Required')
            rec.xuong_minimum = len(optional_lines)

    @api.depends('approv_ids')
    def _compute_user_ids(self):
        for record in self:
            record.user_ids = record.approv_ids.user_id

    @api.depends('line_ids')
    def _compute_user_line_ids(self):
        for record in self:
            record.user_line_ids = record.line_ids.user_id
    
    @api.depends('xuong_ids')
    def _compute_user_xuong_ids(self):
        for record in self:
            record.user_xuong_ids = record.xuong_ids.user_id

    @api.constrains('approv_ids')
    def _constrains_approver_ids(self):
        # There seems to be a problem with how the database is updated which doesn't let use to an sql constraint for this
        # Issue is: records seem to be created before others are saved, meaning that if you originally have only user a
        #  change user a to user b and add a new line with user a, the second line will be created and will trigger the constraint
        #  before the first line will be updated which wouldn't trigger a ValidationError
        for record in self:
            if len(record.approv_ids) != len(record.approv_ids.user_id):
                raise ValidationError(_('An user may not be in the approver list multiple times.'))

    def create_request(self):
        view_id = self.env.ref(
            'multi_level_approval.multi_approval_view_form', False)
        if self.id == 48:
            # return {
            #     'type': 'ir.actions.act_url',
            #     'url': 'https://wl20.woodsland.vn/web#action=670&model=hr.leave&view_type=calendar&cids=1&menu_id=448',
            #     'target': 'new'
            # }
            return change_time_off(self)
        else:
            return {
                'name': _('New Request'),
                'view_mode': 'form',
                'res_model': 'multi.approval',
                'view_id': view_id and view_id.id or False,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_type_id': self.id,
                }
            }

    def open_submitted_request(self):
        if self.id == 48:
            return change_time_off_approval(self)
        else:
            return {
                'name': _(self.name),
                'view_mode': 'tree,form',
                'res_model': 'multi.approval',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('type_id', '=', self.id), ('state', '=', 'Submitted')],
                'context': {
                    'default_type_id': self.id,
                }
            }
