# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright Domiup (<http://domiup.com>).
#
##############################################################################

from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class MultiApprovalLine(models.Model):
    _name = 'multi.approval.line'
    _description = 'Multi Aproval Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence'

    name = fields.Char(string='Title', required=True)
    user_id = fields.Many2one(string='User', comodel_name="res.users",
                              required=True)
    existing_request_user_ids = fields.Many2many('res.users', compute='_compute_existing_request_user_ids')
    sequence = fields.Integer(string='Sequence')
    require_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Người nhận thông tin'),
         ], string="Type of Approval", default='Required')
    approval_id = fields.Many2one(
        string="Approval", comodel_name="multi.approval")
    state = fields.Selection(
        [('Draft', 'Draft'),
         ('Waiting for Approval', 'Waiting for Approval'),
         ('Approved', 'Approved'),
         ('Refused', 'Refused'),
         ('Cancel', 'Cancel'),
         ], default="Draft")
    refused_reason = fields.Text('Refused Reason')
    deadline = fields.Date(string='Deadline')

    # 13.0.1.1
    def set_approved(self):
        self.ensure_one()
        self.state = 'Approved'

    def set_refused(self, reason=''):
        self.ensure_one()
        self.write({
            'state': 'Refused',
            'refused_reason': reason
        })

    @api.depends('approval_id.user_id', 'approval_id.line_ids.user_id')
    def _compute_existing_request_user_ids(self):
        for approver in self:
            approver.existing_request_user_ids = \
                self.mapped('approval_id.line_ids.user_id')._origin \
                | self.approval_id.user_id._origin

    def _create_activity(self):
        for approver in self:
            approver.approval_id.activity_schedule(
                'approvals.mail_activity_data_approval',
                user_id=approver.user_id.id)
    def send_request_approv_mail(self):
        requests = self.approval_id.filtered(
            lambda r: r.type_id.mail_notification and r.line_ids.user_id and
                      r.state == 'Submitted' and r.line_ids.require_opt == 'Optional'
        )

        for req in requests:
            print(req.id)
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
                    'email_to': req.line_ids_user_id.email,
                    'email_from': req.user_id.email,
                    'auto_delete': True,
                    'state': 'outgoing',
                })

    def send_activity_approv_notification(self):
        requests = self.approval_id.filtered(
            lambda r: r.type_id.activity_notification and r.line_ids.user_id and
                r.state == 'Submitted' and r.line_ids.require_opt == 'Optional'
        )
        notify_type = self.env.ref("mail.mail_activity_data_todo", False)
        # print(notify_type)
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
                'user_id': req.line_ids.user_id.id,
            })