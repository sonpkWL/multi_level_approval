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
from datetime import datetime
import logging
from collections import defaultdict
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.addons.iap.tools import iap_tools
from odoo.addons.web.controllers.utils import clean_action
_logger = logging.getLogger(__name__)


class MultiApproval(models.Model):
    _name = 'multi.approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Multi Aproval'

    _check_company_auto = True

    code = fields.Char(default=_('New'))
    name = fields.Char(string='Title', required=True)
    user_id = fields.Many2one(
        string='Request by', comodel_name="res.users",
        required=True, default=lambda self: self.env.uid)
    employee_id = fields.Many2one('hr.employee', string='Employee', compute='_employee')
    priority = fields.Selection(
        [('0', 'Normal'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High')], string='Priority', default='0')
    request_date = fields.Datetime(
        string='Request Date', default=fields.Datetime.now)
    complete_date = fields.Datetime()
    type_id = fields.Many2one(
        string="Type", comodel_name="multi.approval.type", required=True)
    image = fields.Binary(related="type_id.image")
    description = fields.Html('Description')
    state = fields.Selection(
        [('Draft', 'Draft'),
         ('Submitted', 'Submitted'),
         ('Approved', 'Approved'),
         ('Refused', 'Refused'),
         ('Cancel', 'Cancel')], default='Draft', tracking=True)

    document_opt = fields.Selection(
        string="Document opt",
        readonly=True, related='type_id.document_opt')
    attachment_ids = fields.Many2many('ir.attachment', string='Documents')

    contact_opt = fields.Selection(
        string="Contact opt",
        readonly=True, related='type_id.contact_opt')
    contact_id = fields.Many2one('res.partner', string='Contact')

    date_opt = fields.Selection(
        string="Date opt",
        readonly=True, related='type_id.date_opt')
    date = fields.Date('Date')

    period_opt = fields.Selection(
        string="Period opt",
        readonly=True, related='type_id.period_opt')
    date_start = fields.Datetime('Start Date')
    date_end = fields.Datetime('End Date')

    item_opt = fields.Selection(
        string="Item opt",
        related='type_id.item_opt')
    item_id = fields.Many2one('product.product', string='Item', ondelete='cascade', select=True)

    multi_items_opt = fields.Selection(
        string="Multi Items opt",
        readonly=True, related='type_id.multi_items_opt')
    item_ids = fields.One2many('multi.approval.product.line', 'approval_request_id', string='Items', ondelete='cascade', select=True)

    quantity_opt = fields.Selection(
        string="Quantity opt",
        readonly=True, related='type_id.quantity_opt')
    quantity = fields.Float('Quantity')

    amount_opt = fields.Selection(
        string="Amount opt",
        readonly=True, related='type_id.amount_opt')
    amount = fields.Float('Amount')

    payment_opt = fields.Selection(
        string="Payment opt",
        readonly=True, related='type_id.payment_opt')
    payment = fields.Float('Payment')

    reference_opt = fields.Selection(
        string="Reference opt",
        readonly=True, related='type_id.reference_opt')
    reference = fields.Char('Reference')

    location_opt = fields.Selection(
        string="Location opt",
        readonly=True, related='type_id.location_opt')
    location = fields.Char('Location')

    tt_opt = fields.Selection(
        string="TT Item opt",
        readonly=True, related='type_id.tt_opt')
    # # tt_items_line_ids = fields.Char('tt_items')
    tt_line_ids = fields.One2many('multi.approval.item.line', 'multi_approval_id', string='TT Items'
                                  , ondelete='cascade', select=True, index=True)
    tt_id = fields.Many2one('multi.approval.item.line', string="Line", copy=False)

    reason_wl_opt = fields.Selection(
        string="reason wl opt",
        readonly=True, related='type_id.reason_wl_opt')
    reason_wl = fields.Selection([('CaNhan', 'Cá nhân'),
                               ('CongViec', 'Công việc')]
                              , 'Lý do')
    xuong_opt = fields.Selection(
        string="xuong wl opt", readonly=True, related='type_id.xuong_opt')
    xuong = fields.Many2one('xuong.wl', string='Xưởng')
    warehouse_wl_opt = fields.Selection(
         string="warehouse_wl_opt", readonly=True, related='type_id.warehouse_wl_opt')
    warehouse_wl = fields.Many2one('stock.warehouse', string='Kho')
    nhamay_wl_opt = fields.Selection(
        string="warehouse_wl_opt", readonly=True, related='type_id.nhamay_wl_opt')
    nhamay_wl = fields.Many2one('hr.nhamay.wl', string='Nhà máy')
    line_ids = fields.One2many('multi.approval.line', 'approval_id',
                               string="Lines")
    line_id = fields.Many2one('multi.approval.line', string="Line", copy=False)
    approve_lines_ids = fields.Many2many('multi.approval.line', string="Lines")
    lines_ids = fields.Many2many('res.users', string="Approver")
    # approv_ids = fields.One2many('multi.approval.type.line.noti', 'approv_idss', string="Approvers", check_company=True
    #                              , store=True, readonly=False)
    # approv_id = fields.Many2one(
    #     'res.users', string='Approver', related='approv_ids.user_id')
    deadline = fields.Date(string='Deadline', related='line_id.deadline')
    pic_id = fields.Many2one(
        'res.users', string='Approver', related='line_id.user_id')
    is_pic = fields.Boolean(compute='_check_pic')
    follower = fields.Text('Following Users', default='[]', copy=False)

    # copy the idea of hr_expense
    attachment_number = fields.Integer(
        'Number of Attachments', compute='_compute_attachment_number')
    # ticket_properties = fields.PropertiesDefinition('Ticket Properties')
    properties = fields.Properties(
        'Properties', definition='type_id.ticket_properties',
        copy=True)
    nm_id = fields.Selection(
        [('WLTH', 'WL Thuận hưng'),
         ('WLYS', 'WL Yên Sơn'),
         ('WLTB', 'WL Thái Bình'),
         ('WLVF', 'WL Hà Giang')], string='Nhà máy'
    )
    product_category_opt = fields.Selection(
        string="product category opt",
        readonly=True, related='type_id.product_category_opt')
    product_category = fields.Many2one('product.category', 'Nhóm hàng hóa')

    # check_out = fields.Boolean(string='Check out')
    time_out = fields.Datetime(string='Thời gian ra')
    # check_in = fields.Boolean(string='Check in')
    time_in = fields.Datetime(string='Thời gian vào')
    bvnm = fields.Many2one('res.users', string='Bảo vệ')
    is_bvnm = fields.Boolean(compute='_check_pic_bvnm')

    @api.depends("user_id")
    def _employee(self):
        for r in self:
            r.employee_id = self.env['hr.employee'].search([('user_id', '=', r.user_id.id)], limit=1)

    def check_out(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.time_out:
            return self.write({'time_in': current_time})
        else:
            return self.write({'time_out': current_time})
        
    @api.depends_context("uid")
    def _check_pic_bvnm(self):
        for r in self:
            ds = r.lines_ids
            r.is_bvnm = False
            for res in ds:
                dsbv = self.env['hr.employee'].search([('user_id', '=', res.id), ('category_ids', '=', 1)], limit=1)
                if dsbv.user_id.id == self.env.uid == res.id:
                    r.is_bvnm = True
                    break

    @api.depends_context("uid")
    def _check_pic(self):
        for r in self:
            current_user_id = self.env.user.id
            ds = r.lines_ids
            r.is_pic = False
            for res in ds:
                if current_user_id == res.id:
                    r.is_pic = True
                    break
            # r.is_pic = r.pic_id.id == self.env.uid

    # request.type_id.manager_approval == 'Required' if manager_user == user.id else False
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'multi.approval'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])

        attachment = dict((data['res_id'], data['res_id_count'])
                          for data in attachment_data)
        for r in self:
            r.attachment_number = attachment.get(r.id, 0)


    def action_cancel(self):
        recs = self.filtered(lambda x: x.state == 'Draft')
        rec = self.filtered(lambda x: x.state in ['Submitted', 'Approved'])
        is_manager = self.user_has_groups('multi_level_approval.group_approval_manager')
        if rec and is_manager:
            rec.write({'state': 'Cancel'})
        elif recs:
            recs.write({'state': 'Cancel'})

    def action_submit(self):
        recs = self.filtered(lambda x: x.state == 'Draft')
        if self.type_id.manager_approval == 'Required':
            employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
            if not employee.parent_id:
                raise UserError(_('This request needs to be approved by your manager. There is no manager linked to your employee profile.'))
            if not employee.parent_id.user_id:
                raise UserError(_('This request needs to be approved by your manager. There is no user linked to your manager.'))

        for r in recs:
            # Check if document is required
            if r.document_opt == 'Required' and r.attachment_number < 1:
                raise UserError(_('Document is required !'))
            if not r.type_id.line_ids and not self.type_id.manager_approval == 'Required':
                raise UserError(_(
                    'There is no approver of the type "{}" !'.format(
                        r.type_id.name)))
            r.state = 'Submitted'


        recs.send_approval_requests_to_users()
        recssa = recs.line_ids.filtered(lambda x: x.require_opt == 'Optional')
        # recss = recs.approv_ids.filtered(lambda x: x.require_opt == 'Optional')
        for rec in recssa:
            recs.update_follower(rec.user_id.id)
        # self.message_post(body=_(recss))
        # self.message_post(body=_(recssa))
        # recssa._create_activity()
        # recssa.send_request_approv_mail()
        # recssa.send_activity_approv_notification()
        # recssa.sudo().write({'state': 'Waiting for Approval'})

        if self.type_id.user_xuong_opt:
            recs._create_xuong_lines()
        else:
            recs._create_approval_lines()
        recs.send_request_mail()
        # recs.send_request_approv_mail_test()
        recs.send_activity_notification()
        # recs.send_activity_approv_notification_test()

        print(recs.pic_id)
        print(recs.line_id.id)
        print(recs.line_ids.user_id)
        #     recs._create_approv_lines()
        #     recs.send_request_mail()
        #     recs.send_activity_notification()

        # lines = self.line_ids.filtered(lambda x: x.require_opt == 'Optional')

        # if recs.type_id.approv_ids:
        #     recs = self.filtered(lambda x: x.line_ids.require_opt == 'Optional')
        # if not lines:

        # if not isinstance(approver, models.BaseModel):
        #     approver = self.mapped('line_ids').filtered(
        #         lambda approver: approver.user_id == self.env.user and approver.require_opt == 'Optional'
        #     )
        # # approver.write({'status': 'approved'})

        # else:
        #     recs._create_approval_lines()
        #     recs.send_request_mail()
        #     recs.send_activity_notification()
        # approvers = self.type_id.
        # if approvers:
        #     approvers = approvers.filtered(lambda x: x.sequence == 1000)
        # recs.send_approval_requests_to_users()
        # approvers.send_request_approv_mail()
        # approvers.send_activity_approv_notification()
        # approvers = self.filtered(lambda x:
        # x.state == 'Draft' and (x.sequence == 1000))
        # if recs.filtered(lambda a: a.sequence == 1000):
        #     recs._compute_approv_ids()
        #     recs.send_request_mail()
        #     recs.send_activity_notification()
    # def action_submit(self):
    #     recs = self.filtered(lambda x: x.state == 'Draft')
    #     if self.type_id.manager_approval == 'Required':
    #         employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
    #         if not employee.parent_id:
    #             raise UserError(_('This request needs to be approved by your manager. There is no manager linked to your employee profile.'))
    #         if not employee.parent_id.user_id:
    #             raise UserError(_('This request needs to be approved by your manager. There is no user linked to your manager.'))
    #
    #     for r in recs:
    #         # Check if document is required
    #         if r.document_opt == 'Required' and r.attachment_number < 1:
    #             raise UserError(_('Document is required !'))
    #         if not r.type_id.line_ids:
    #             raise UserError(_(
    #                 'There is no approver of the type "{}" !'.format(
    #                     r.type_id.name)))
    #         r.state = 'Submitted'
    #     lines = recs.line_ids.filtered(lambda x: x.require_opt == 'Optional')
    #     if lines:
    #     # if not lines:
    #     # recs._create_approv_lines()
    #         lines._create_approval_lines()
    #         lines.send_request_mail()
    #         lines.send_activity_notification()

    @api.model
    def get_follow_key(self, user_id=None):
        if not user_id:
            user_id = self.env.uid
        k = '[res.users:{}]'.format(user_id)
        return k

    def update_follower(self, user_id):
        self.ensure_one()
        k = self.get_follow_key(user_id)
        follower = self.follower
        if k not in follower:
            self.follower = follower + k

    # 13.0.1.1
    def set_approved(self):
        self.ensure_one()
        self.state = 'Approved'
        self.complete_date = fields.Datetime.now()
        self.send_approved_mail()

    def set_refused(self, reason=''):
        self.ensure_one()
        self.state = 'Refused'
        self.complete_date = fields.Datetime.now()
        self.send_refused_mail()

    def action_approve(self):
        ret_act = None
        recs = self.filtered(lambda x: x.state == 'Submitted')
        dk = False
        for rec in recs:
            if not rec.is_pic:
                msg = _('{} do not have the authority to approve this request !'.format(rec.env.user.name))
                self.sudo().message_post(body=msg)
                return False
            app_lines_ids = rec.approve_lines_ids
            for line in app_lines_ids:
                # lines = line.line_id

                if not line or line.state != 'Waiting for Approval':
                    # Something goes wrong!
                    self.message_post(body=_('Something goes wrong!'))
                    return False

            # approv_lines = rec.line_ids.filtered(
            #     lambda x: x.sequence >= line.sequence and x.state == 'Draft' and x.require_opt == 'Optional')
            # if approv_lines:
            #     next_line = approv_lines.sorted('sequence')
            #     rec.line_id = next_line
            #     rec.send_request_mail()
            #     recs.send_activity_notification()

            # Update follower
                rec.update_follower(self.env.uid)

                if line.user_id.id == self.env.uid:
                    dk = True
                    line.set_approved()
                    break
            if dk:
                # check if this line is required
                other_lines = rec.line_ids.filtered(
                    lambda x: x.sequence >= line.sequence and x.state == 'Draft' and x.require_opt == 'Required')
                if not other_lines:
                    ret_act = rec.set_approved()
                else:
                    sttt = min(other_lines.sorted(key=lambda x: x.sequence))
                    print('stt: ', sttt.sequence)
                    next_line = other_lines.filtered(lambda x: x.sequence == sttt.sequence)
                    print('sequence: ', next_line)
                    rec.write({
                        'lines_ids': [(5, 0, 0)],  # Trường Many2many sẽ được gán bằng một danh sách rỗng
                        'approve_lines_ids': [(5, 0, 0)]
                    })
                    # users_to_approv = defaultdict(lambda: self.env['multi.approval.line'])
                    for r in next_line:

                        r.write({
                            'state': 'Waiting for Approval',
                        })
                        rec.approve_lines_ids += r
                        rec.lines_ids += r.user_id
                        rec.line_id = r
                    rec.send_request_mail()
                    rec.send_activity_notification()

                    # rec.line_ids.send_request_approv_mail()
                    # recs.line_ids.send_activity_approv_notification()
                    print('Test phe duyet')
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if rec.is_bvnm:
                    return self.write({'time_out': current_time})
                msg = _('I approved')
                rec.finalize_activity_or_message('approved', msg)
            if ret_act:
                return ret_act
            return True

    def action_refuse(self, reason=''):
        ret_act = None
        recs = self.filtered(lambda x: x.state == 'Submitted')
        dk = False
        for rec in recs:
            if not rec.is_pic:
                msg = _('{} do not have the authority to approve this request !'.format(rec.env.user.name))
                self.sudo().message_post(body=msg)
                return False
            app_lines_ids = rec.approve_lines_ids
            for line in app_lines_ids:
                if not line or line.state != 'Waiting for Approval':
                    # Something goes wrong!
                    self.message_post(body=_('Something goes wrong!'))
                    return False

            # Update follower
                rec.update_follower(self.env.uid)
                dk = True
                break
            if dk:
                # check if this line is required
                if line.require_opt == 'Required':
                    ret_act = rec.set_refused(reason)
                    draft_lines = rec.line_ids.filtered(lambda x: x.state == 'Draft')
                    if draft_lines:
                        draft_lines.state = 'Cancel'
                else:  # optional
                    other_lines = rec.line_ids.filtered(
                        lambda x: x.sequence >= line.sequence and x.state == 'Draft')
                    if not other_lines:
                        ret_act = rec.set_refused(reason)
                    else:
                        sttt = min(other_lines.sorted(key=lambda x: x.sequence))
                    print('stt: ', sttt.sequence)
                    next_line = other_lines.filtered(lambda x: x.sequence == sttt.sequence)
                    print('sequence: ', next_line)
                    rec.write({
                        'lines_ids': [(5, 0, 0)],  # Trường Many2many sẽ được gán bằng một danh sách rỗng
                        'approve_lines_ids': [(5, 0, 0)]
                    })
                    # users_to_approv = defaultdict(lambda: self.env['multi.approval.line'])
                    for r in next_line:

                        r.write({
                            'state': 'Waiting for Approval',
                        })
                        rec.approve_lines_ids += r
                        rec.lines_ids += r.user_id
                        rec.line_id = r
                line.set_refused(reason)
                msg = _('I refused due to this reason: {}'.format(reason))
                rec.finalize_activity_or_message('refused', msg)
            if ret_act:
                return ret_act

    def finalize_activity_or_message(self, action, msg):
        requests = self.filtered(
            lambda r: r.type_id.activity_notification
        )
        # print('Test 1')
        # print(requests)
        notify_type = self.env.ref("mail.mail_activity_data_todo", False)
        if requests and notify_type: 
            activities = requests.mapped("activity_ids").filtered(
                lambda a: a.activity_type_id == notify_type and a.user_id == self.env.user)
            activities._action_done(msg)
            # print(activities)
        requests2 = self - requests
        if requests2:
            requests2.message_post(body=msg)

    def _create_approv_lines(self):
        ApprovalLine = self.env['multi.approval.line']
        for r in self:
            if r.type_id.user_ids:
                ds_noti = r.type_id.approv_ids
                ds = 0
                for line in ds_noti:
                    ds = ds + 1
                    vals = {
                        'name': line.user_id.name,
                        'user_id': line.user_id.id,
                        'sequence': ds + 1000,
                        'require_opt': line.require_opt,
                        'approval_id': r.id
                    }
                    # if line == ds_noti[0]:
                    #     vals.update({'state': 'Waiting for Approval'})
                    approv = ApprovalLine.create(vals)
                    # if line == ds_noti[0]:
                    r.line_id = approv
    ## Tạm đóng code cũ
    # def _create_approval_lines(self):
    #     ApprovalLine = self.env['multi.approval.line']
    #     for r in self:
    #         lines = r.type_id.line_ids.sorted('sequence')
    #         nmwl = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).nhamaywl
    #         ##  security approvals
    #         if r.type_id.NM_opt:
    #             emp_nm = self.env['hr.employee'].search([('nhamaywl', '=', nmwl.id), ('description', 'like', 'BVNM')],
    #                                                     limit=1)
    #             if emp_nm.user_id:
    #                 self.bvnm = emp_nm.user_id.id
    #                 vals = {
    #                     'name': emp_nm.user_id.name,
    #                     'user_id': emp_nm.user_id.id,
    #                     'sequence': 99,
    #                     'require_opt': 'Required',
    #                     'approval_id': r.id
    #                 }
    #                 approval = ApprovalLine.create(vals)
    #                 r.line_id = approval
    #         ##  Manager approvals
    #         manager_user = 0
    #         if r.type_id.manager_approval:
    #             employee = self.env['hr.employee'].search([('user_id', '=', r.user_id.id)], limit=1)
    #             if employee.parent_id.user_id:
    #                 manager_user = employee.parent_id.user_id.id
    #                 vals = {
    #                     'name': employee.parent_id.user_id.name,
    #                     'user_id': manager_user,
    #                     'sequence': 0,
    #                     'require_opt': 'Required',
    #                     'approval_id': r.id
    #                 }
    #                 vals.update({'state': 'Waiting for Approval'})
    #                 approval = ApprovalLine.create(vals)
    #                 r.line_id = approval
    #         last_seq = 0
    #         last_sequ = 0
    #         if r.type_id.type_approval:
    #             if r.type_id.line_ids.product_category:
    #                 emp = r.type_id.line_ids.search([('product_category', '=', r.product_category.id)
    #                                                     , ('nhamaywl', 'like', nmwl.id)])
    #                 for e in emp:
    #                     line_sequ = e.sequence
    #                     if not line_sequ or line_sequ <= last_sequ:
    #                         line_sequ = line_sequ + 1
    #                     last_sequ = line_sequ
    #                     vals = {
    #                         'name': e.user_id.name,
    #                         'user_id': e.get_user(),
    #                         'sequence': line_sequ,
    #                         'require_opt': e.require_opt,
    #                         'approval_id': r.id
    #                     }
    #                     if not r.type_id.manager_approval:
    #                         if e == emp[0]:
    #                             vals.update({'state': 'Waiting for Approval'})
    #                     approval = ApprovalLine.create(vals)
    #                     if not r.type_id.manager_approval:
    #                         if e == emp[0]:
    #                             r.line_id = approval
    #             else:
    #                 emp2 = r.type_id.line_ids.search([('nhamaywl', 'like', nmwl.id)])
    #                 for e2 in emp2:
    #                     line_seq = e2.sequence
    #                     if not line_seq or line_seq <= last_seq:
    #                         line_seq = last_seq + 1
    #                     last_seq = line_seq
    #                     vals = {
    #                         'name': e2.user_id.name,
    #                         'user_id': e2.get_user(),
    #                         'sequence': line_seq,
    #                         'require_opt': e2.require_opt,
    #                         'approval_id': r.id
    #                     }
    #                     if not r.type_id.manager_approval:
    #                         if e2 == emp2[0]:
    #                             vals.update({'state': 'Waiting for Approval'})
    #                     approval = ApprovalLine.create(vals)
    #                     if not r.type_id.manager_approval:
    #                         if e2 == emp2[0]:
    #                             r.line_id = approval
    #         else:
    #             for l in lines:
    #                 line_seq = l.sequence
    #                 if not line_seq or line_seq <= last_seq:
    #                     line_seq = last_seq + 1
    #                 last_seq = line_seq
    #                 vals = {
    #                     'name': l.user_id.name,
    #                     'user_id': l.get_user(),
    #                     'sequence': line_seq,
    #                     'require_opt': l.require_opt,
    #                     'approval_id': r.id
    #                 }
    #                 if not r.type_id.manager_approval:
    #                     if l == lines[0]:
    #                         vals.update({'state': 'Waiting for Approval'})
    #                 approval = ApprovalLine.create(vals)
    #                 if not r.type_id.manager_approval:
    #                     if l == lines[0]:
    #                         r.line_id = approval

    ## Code người phê duyệt theo nhóm                        
    @api.depends('line_ids')
    def _create_approval_lines(self):
        ApprovalLine = self.env['multi.approval.line']
        for request in self:
            approv_type = request.type_id
            # Don't remove manually added approvers
            lines = request.type_id.line_ids.sorted('stt')
            users_to_approv = defaultdict(lambda: self.env['multi.approval.line'])
            users_to_category_approv = defaultdict(lambda: self.env['multi.approval.type.line'])
            if request.nhamay_wl:
                nmwl = request.nhamay_wl
            else:
                nmwl = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).nhamaywl
        #  Manager approvals
            manager_user = 0
            if request.type_id.manager_approval:
                employee = self.env['hr.employee'].search([('user_id', '=', request.user_id.id)], limit=1)
                if employee.parent_id.user_id:
                    manager_user = employee.parent_id.user_id.authority_id.id if employee.parent_id.user_id.authority_id.id else employee.parent_id.user_id.id
                    manager_user_name = employee.parent_id.user_id.authority_id.name if employee.parent_id.user_id.authority_id.name else employee.parent_id.user_id.name
                    sequence = request.type_id.manager_stt if request.type_id.manager_approval == 'Required' else 101
                    manager_name = request.type_id.manager_name
                    vals = {
                        'name': manager_name if manager_name else manager_user_name,
                        'user_id': manager_user,
                        'sequence': sequence,
                        'require_opt': request.type_id.manager_approval,
                        'approval_id': request.id
                    }
                    # vals.update({'state': 'Waiting for Approval'})
                    approval = ApprovalLine.create(vals)
                    # request.line_id = approval
                    # request.approve_lines_ids = approval
                    # request.lines_ids = approval.user_id
        ##  quanly approvals
            quanly_approval = 0
            if request.type_id.quanly_approval:
                employee = self.env['hr.employee'].search([('user_id', '=', request.user_id.id)], limit=1)
                # Check có coach không, coach có khác manager k
                if employee.coach_id.user_id and employee.parent_id.user_id != employee.coach_id.user_id:
                    sequence = request.type_id.quanly_stt if request.type_id.quanly_approval == 'Required' else 102
                    quanly_approval = employee.coach_id.user_id.authority_id.id if employee.coach_id.user_id.authority_id.id else employee.coach_id.user_id.id
                    quanly_approval_name = employee.coach_id.user_id.authority_id.name if employee.coach_id.user_id.authority_id.name else employee.coach_id.user_id.name
                    quanly_name = request.type_id.quanly_name
                    vals = {
                        'name': quanly_name if quanly_name else quanly_approval_name,
                        'user_id': quanly_approval,
                        'sequence': sequence,
                        'require_opt': request.type_id.quanly_approval,
                        'approval_id': request.id
                    }
                    approval = ApprovalLine.create(vals)
        ## Lines
            # check có áp dụng điều kiện k?
            if request.type_id.type_approval:
                # Check ĐK theo xưởng
                if request.xuong:
                    emp = request.type_id.line_ids.search([('nhamaywl', 'like', nmwl.id),
                                                           ('xuong', 'like', request.xuong.id),
                                                           ('type_id', '=', approv_type.id)])
                    approv_id_vals = []
                    new_users = emp.browse([])
                    for approv in emp:
                        users_to_category_approv[approv.user_id.id] |= approv
                        print('line user:', users_to_category_approv[approv.user_id.id])
                        ## Check ĐK theo tiền
                        if approv.check_amount:
                            if approv.type_values == 'between':
                                if approv.search([('user_id', '=', approv.user_id.id),
                                                  ('gt1', '>', request.amount),
                                                  ('gt2', '<', request.amount),
                                                  ('type_id', '=', approv_type.id)]):
                                    print('between:', approv.user_id.name)
                                    new_users |= approv
                            elif approv.search([('user_id', '=', approv.user_id.id),
                                                ('gt1', approv.type_values, request.amount),
                                                ('type_id', '=', approv_type.id)]):
                                print('line approval:', approv)
                                new_users |= approv
                        else:
                            new_users |= approv
                    # sequence = 1000
                    for user in new_users:
                        required = users_to_category_approv[user.user_id.id].require_opt
                        title = users_to_category_approv[user.user_id.id].name
                        stt = users_to_category_approv[user.user_id.id].stt
                        current_approv = users_to_approv[user.user_id.id]
                        # sequence += 1
                        if not current_approv:
                            approv_id_vals = {
                                'name': title if title else user.user_id.name,
                                'user_id': user.user_id.id,
                                'sequence': stt,
                                'require_opt': required,
                                'approval_id': request.id
                            }
                            # if not request.type_id.manager_approval:
                            #     if user == new_users[0]:
                            #         approv_id_vals.update({'state': 'Waiting for Approval'})
                            approval = ApprovalLine.create(approv_id_vals)
                            # if not request.type_id.manager_approval:
                            #     if user == new_users[0]:
                            #         request.line_id = approval
                            #         request.approve_lines_ids = approval
                            #         request.lines_ids = approval.user_id
                # end check theo xưởng
                else:
                    emp2 = request.type_id.line_ids.search([('nhamaywl', 'like', nmwl.id),
                                                            ('type_id', '=', approv_type.id)])
                    print('emp2:', emp2)
                    new_users = emp2.browse([])
                    for approv in emp2:
                        users_to_category_approv[approv.user_id.id] |= approv
                        print('line user:', users_to_category_approv[approv.user_id.id])
                        ## Check ĐK theo tiền
                        if approv.check_amount:
                            if approv.type_values == 'between':
                                if approv.search([('user_id', '=', approv.user_id.id),
                                                  ('gt1', '>', request.amount),
                                                  ('gt2', '<', request.amount),
                                                  ('type_id', '=', approv_type.id)]):
                                    print('between:', approv.user_id.name)
                                    new_users |= approv
                            elif approv.search([('user_id', '=', approv.user_id.id),
                                                ('gt1', approv.type_values, request.amount),
                                                ('type_id', '=', approv_type.id)]):
                                print('line approval:', approv)
                                new_users |= approv
                        else:
                            new_users |= approv
                    approv_id_vals = []
                    # sequence = 1000
                    for user in new_users:
                        required = users_to_category_approv[user.user_id.id].require_opt
                        title = users_to_category_approv[user.user_id.id].name
                        stt = users_to_category_approv[user.user_id.id].stt
                        current_approv = users_to_approv[user.user_id.id]
                        print('user name: ', user.user_id.name)
                        # sequence += 1
                        if not current_approv:
                            approv_id_vals = {
                                'name': title if title else user.user_id.name,
                                'user_id': user.user_id.id,
                                'sequence': stt,
                                'require_opt': required,
                                'approval_id': request.id
                            }
                            # if not request.type_id.manager_approval:
                            #     if user == new_users[0]:
                            #         approv_id_vals.update({'state': 'Waiting for Approval'})
                            approval = ApprovalLine.create(approv_id_vals)
                            # if not request.type_id.manager_approval:
                            #     if user == new_users[0]:
                            #         request.line_id = approval
                            #         request.approve_lines_ids = approval
                            #         request.lines_ids = approval.user_id

            else:
                for approv in lines:
                    users_to_category_approv[approv.user_id.id] |= approv
                new_users = request.type_id.user_line_ids
                approv_id_vals = []
                # sequence = 1000
                for user in new_users:
                    required = users_to_category_approv[user.id].require_opt
                    title = users_to_category_approv[user.id].name
                    stt = users_to_category_approv[user.id].stt
                    current_approv = users_to_approv[user.id]
                    # sequence += 1
                    if not current_approv:
                        approv_id_vals = {
                            'name': title if title else user.name,
                            'user_id': user.id,
                            'sequence': stt,
                            'require_opt': required,
                            'approval_id': request.id
                        }
                        # if not request.type_id.manager_approval:
                        #     if user == new_users[0]:
                        #         approv_id_vals.update({'state': 'Waiting for Approval'})
                        approval = ApprovalLine.create(approv_id_vals)
                        # if not request.type_id.manager_approval:
                        #     if user == new_users[0]:
                        #         request.line_id = approval
                        #         request.approve_lines_ids = approval
                        #         request.lines_ids = approval.user_id
        ## Quản lý kho phê duyệt
            if request.type_id.warehouse_approval and request.warehouse_wl:
                warehouse = self.env['stock.warehouse'].search([('id', '=', request.warehouse_wl.id)], limit=1)
                if warehouse.user_id:
                    sequence = request.type_id.warehouse_stt if request.type_id.warehouse_approval == 'Required' else 103
                    warehouse_user_id = warehouse.user_id.authority_id.id if warehouse.user_id.authority_id.id else warehouse.user_id.id
                    warehouse_user_name = warehouse.user_id.authority_id.name if warehouse.user_id.authority_id.name else warehouse.user_id.name
                    warehouse_name = request.type_id.warehouse_name
                    vals = {
                        'name': warehouse_name if warehouse_name else warehouse_user_name,
                        'user_id': warehouse_user_id,
                        'sequence': sequence,
                        'require_opt': request.type_id.warehouse_approval,
                        'approval_id': request.id
                    }
                    approval = ApprovalLine.create(vals)

        ##  security approvals
            if request.type_id.NM_opt:
                emp_nm = self.env['hr.employee'].search([('nhamaywl', '=', nmwl.id),
                                                         ('description', 'like', 'BVNM')], limit=1)
                if emp_nm.user_id:
                    self.bvnm = emp_nm.user_id.id
                    vals = {
                        'name': emp_nm.user_id.name,
                        'user_id': emp_nm.user_id.id,
                        'sequence': 100,
                        'require_opt': 'Required',
                        'approval_id': request.id
                    }
                    approval = ApprovalLine.create(vals)
            ## Lọc người đầu tiên vào luồng phê duyệt
            approval_line = self.env['multi.approval.line'].search([('approval_id', '=', self.id),
                                                                    ('require_opt', '=', 'Required')])
            user_line = min(approval_line.sorted(key=lambda x: x.sequence))
            next_line = approval_line.filtered(lambda x: x.sequence == user_line.sequence)
            print('line approval: ', next_line)
            for line in next_line:
                line.update({'state': 'Waiting for Approval'})
                request.line_id = line
                request.approve_lines_ids |= line
                request.lines_ids |= line.user_id

    # ## Lọc ĐK người duyệt theo xưởng
    # @api.depends('line_ids')
    # def _create_xuong_lines(self):
    #     ApprovalLine = self.env['multi.approval.line']
    #     for request in self:
    #         approv_type = request.type_id
    #         lines = request.type_id.xuong_ids.sorted('sequence')
    #         users_to_approv = defaultdict(lambda: self.env['multi.approval.line'])
    #         users_to_category_approv = defaultdict(lambda: self.env['multi.approval.type.line.xuong'])
    #         nmwl = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).nhamaywl
    #         emp = request.type_id.xuong_ids.search([('nhamaywl', 'like', nmwl.id),
    #                                                 ('xuong', 'like', request.xuong.id),
    #                                                ('type_id', '=', approv_type.id)])
    #         for approv in lines:
    #             users_to_category_approv[approv.user_id.id] |= approv
    #         new_users = emp
    #         approv_id_vals = []
    #         sequence = 2
    #         for user in new_users:
    #             required = users_to_category_approv[user.user_id.id].require_opt
    #             title = users_to_category_approv[user.user_id.id].name
    #             # stt = users_to_category_approv[user.id].stt
    #             current_approv = users_to_approv[user.user_id.id]
    #             sequence += 1
    #             if not current_approv:
    #                 approv_id_vals = {
    #                     'name': title if title else user.user_id.name,
    #                     'user_id': user.user_id.id,
    #                     'sequence': sequence,
    #                     'require_opt': required,
    #                     'approval_id': request.id
    #                 }
    #                 approval = ApprovalLine.create(approv_id_vals)
    #         ## Lọc người đầu tiên vào luồng phê duyệt
    #         approval_line = self.env['multi.approval.line'].search([('approval_id', '=', self.id),
    #                                                                 ('require_opt', '=', 'Required')])
    #         user_line = min(approval_line.sorted(key=lambda x: x.sequence))
    #         next_line = approval_line.filtered(lambda x: x.sequence == user_line.sequence)
    #         print('line approval: ', next_line)
    #         for line in next_line:
    #             line.update({'state': 'Waiting for Approval'})
    #             request.line_id = line
    #             request.approve_lines_ids |= line
    #             request.lines_ids |= line.user_id

## Người nhận thông tin
    @api.depends('approv_ids')
    def send_approval_requests_to_users(self):
        ApprovalLine = self.env['multi.approval.line']
        for request in self:
            approv_type = request.type_id
            # Don't remove manually added approvers
            # lines = request.type_id.approv_ids.sorted('sequence')
            users_to_approv = defaultdict(lambda: self.env['multi.approval.line'])
            users_to_category_approv = defaultdict(lambda: self.env['multi.approval.type.line.noti'])
            nmwl = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).nhamaywl
            ## Lines
        ## check có áp dụng điều kiện k?
            if request.type_id.type_approval:
                # Check ĐK theo nhóm hàng
                if request.xuong:
                    emp = request.type_id.approv_ids.search([('xuong', 'like', request.xuong.id),
                                                             ('nhamaywl', 'like', nmwl.id),
                                                             ('approv_id', '=', approv_type.id)])
                    for approv in emp:
                        users_to_category_approv[approv.user_id.id] |= approv
                    new_users = emp
                    approv_id_vals = []
                    sequence = 104
                    for user in new_users:
                        required = users_to_category_approv[user.user_id.id].require_opt
                        title = users_to_category_approv[user.user_id.id].name
                        # stt = users_to_category_approv[user.user_id.id].stt
                        current_approv = users_to_approv[user.user_id.id]
                        sequence += 1
                        if not current_approv:
                            approv_id_vals = {
                                'name': title if title else user.user_id.name,
                                'user_id': user.user_id.id,
                                'sequence': sequence,
                                'require_opt': required,
                                'approval_id': request.id
                            }
                            approval = ApprovalLine.create(approv_id_vals)
                            # request.line_id = approv_id_vals
                # end check theo nhóm
                else:
                    emp2 = request.type_id.approv_ids.search([('nhamaywl', 'like', nmwl.id),
                                                              ('approv_id', '=', approv_type.id)])

                    for approv in emp2:
                        users_to_category_approv[approv.user_id.id] |= approv
                    new_users = emp2
                    approv_id_vals = []
                    sequence = 104
                    for user in new_users:
                        required = users_to_category_approv[user.user_id.id].require_opt
                        title = users_to_category_approv[user.user_id.id].name
                        # stt = users_to_category_approv[user.user_id.id].stt
                        current_approv = users_to_approv[user.user_id.id]
                        print('user name: ', user.name)
                        sequence += 1
                        if not current_approv:
                            approv_id_vals = {
                                'name': title if title else user.user_id.name,
                                'user_id': user.user_id.id,
                                'sequence': sequence,
                                'require_opt': required,
                                'approval_id': request.id
                            }
                            approval = ApprovalLine.create(approv_id_vals)
        ## End check áp dụng ĐK
            else:
                for approv in request.type_id.approv_ids:
                    users_to_category_approv[approv.user_id.id] |= approv
                new_users = request.type_id.user_ids
                approv_id_vals = []
                sequence = 104
                for user in new_users:
                    required = users_to_category_approv[user.id].require_opt
                    title = users_to_category_approv[user.id].name
                    # stt = users_to_category_approv[user.id].stt
                    current_approv = users_to_approv[user.id]
                    sequence += 1
                    if not current_approv:
                        approv_id_vals = {
                            'name': title if title else user.name,
                            'user_id': user.id,
                            'sequence': sequence,
                            'require_opt': required,
                            'approval_id': request.id
                        }
                        approval = ApprovalLine.create(approv_id_vals)
                    
    def _create_activity(self):
        for approver in self:
            approver.type_id.activity_schedule(
                'approvals.mail_activity_data_approval',
                user_id=approver.user_id.id)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            seq_date = vals.get('request_date', fields.Datetime.now())
            vals['code'] = self.env['ir.sequence'].next_by_code(
                'multi.approval', sequence_date=seq_date) or _('New')
        result = super(MultiApproval, self).create(vals_list)
        return result

    # 12.0.1.3
    def send_request_mail(self):
        requests = self.filtered(
            lambda r: r.type_id.mail_notification and r.state == 'Submitted'
        )
        for req in requests:
            if req.type_id.mail_template_id:
                req.type_id.mail_template_id.send_mail(req.id, force_send=True)
            else:
                for r in req.lines_ids:
                    message = self.env['mail.message'].create({
                        'subject': _('Request the approval for: {request_name}').format(
                            request_name=req.display_name
                        ),
                        'model': req._name,
                        'res_id': req.id,
                        'body': self.description,
                        'partner_ids': [(4, r.partner_id.id)],
                        'message_type': 'notification',  # Loại thông báo (notification, comment, email, ...)
                        'author_id': self.env.user.partner_id.id,  # ID của tác giả thông báo
                    })
                    notification = self.env['mail.notification'].sudo().create({
                            'mail_message_id': message.id,
                            'res_partner_id': r.partner_id.id,
                            'notification_type': 'inbox',
                            'notification_status': 'ready',
                            'is_read': False,
                        })
                    mail_value = self.env['mail.mail'].sudo().create({
                        'mail_message_id': message.id,
                        'body_html': self.description,
                        'email_to': req.user_id.email,
                        'email_from': 'no-reply@woodsland.vn',
                        'auto_delete': True,
                        'state': 'outgoing',
                    })
                    mail_value.send()

    def send_request_approv_mail_test(self):
        requests = self.filtered(
            lambda r: r.type_id.mail_notification and r.line_ids.user_id and
                      r.state == 'Submitted' and r.line_ids.require_opt == 'Optional'
        )
        for req in requests:
            if req.type_id.mail_template_id:
                req.type_id.mail_template_id.send_mail(req.id)
            else:
                message = self.env['mail.message'].create({
                    'subject': _('Request the approval for: {request_name}').format(
                        request_name=req.display_name
                    ),
                    'model': req._name,
                    'res_id': req.id,
                    'body': self.description,
                })

                self.env['mail.mail'].sudo().create({
                    'mail_message_id': message.id,
                    'body_html': self.description,
                    'email_to': req.line_ids.user_id.email,
                    'email_from': req.user_id.email,
                    'auto_delete': True,
                    'state': 'outgoing',
                })

    def send_approved_mail(self):
        requests = self.filtered(
            lambda r: r.type_id.approve_mail_template_id and
                r.state == 'Approved'
        )

        for req in requests:
            req.type_id.approve_mail_template_id.send_mail(req.id, force_send=True)
            print('A')

    def send_refused_mail(self):
        requests = self.filtered(
            lambda r: r.type_id.refuse_mail_template_id and
                r.state == 'Refused'
        )
        for req in requests:
            req.type_id.refuse_mail_template_id.send_mail(req.id, force_send=True)

    def send_activity_notification(self):
        requests = self.filtered(
            lambda r: r.type_id.activity_notification and r.state == 'Submitted'
        )
        notify_type = self.env.ref("mail.mail_activity_data_todo", False)
        if not notify_type:
            return
        for req in requests:
            for r in req.lines_ids:
                summary = _("The request {code} need to be reviewed").format(
                    code=req.code
                )
                self.env['mail.activity'].create({
                    'res_id': req.id,
                    'res_model_id': self.env['ir.model']._get(req._name).id,
                    'activity_type_id': notify_type.id,
                    'summary': summary,
                    'user_id': r.id,
                })

    def send_activity_approv_notification_test(self):
        requests = self.filtered(
            lambda r: r.type_id.activity_notification and r.line_ids.user_id and
                      r.state == 'Submitted' and r.line_ids.require_opt == 'Optional'
        )
        # print('B')
        # print(requests.line_ids.user_id)
        notify_type = self.env.ref("mail.mail_activity_data_todo", False)
        if not notify_type:
            return
        for req in requests:
            summary = _("The request {code} need to be reviewed").format(
                code=req.code
            )
            self.env['mail.activity'].create({
                'res_id': req.id,
                'res_model_id': self.env['ir.model']._get(req._name).id,
                'activity_type_id': notify_type.id,
                'summary': summary,
                'user_id': req.line_ids.user_id,
            })


    def action_printer_approval(self):
        return self.env.ref('multi_level_approval.report_approval').report_action(self)
