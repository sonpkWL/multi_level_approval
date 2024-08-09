from odoo import models, fields, api, tools, _
import io
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ReportMultiApproval(models.Model):
    _name = "report.multi.approval.ra.cong"
    _auto = False
    _order = 'request_date DESC'

    code = fields.Char(string='Mã', readonly=True)
    name = fields.Char(string='Tiêu đề', readonly=True)
    description = fields.Html('Mô tả', readonly=True)
    request_date = fields.Datetime(string='Ngày yêu cầu', readonly=True)
    date_start = fields.Datetime(string='Thời gian từ', readonly=True)
    date_end = fields.Datetime(string='Thời gian đến', readonly=True)
    reason_wl = fields.Selection([('CaNhan', 'Cá nhân'),
                                  ('CongViec', 'Công việc')]
                                 , 'Lý do', readonly=True)
    state = fields.Selection(
        [('Draft', 'Draft'),
         ('Submitted', 'Submitted'),
         ('Approved', 'Approved'),
         ('Refused', 'Refused'),
         ('Cancel', 'Cancel')], string='Trạng thái', readonly=True)
    mnv = fields.Char('Mã nhân viên', readonly=True)
    user_id = fields.Many2one('res.users', string='Người tạo', readonly=True)
    nha_may = fields.Many2one('hr.nhamay.wl', string='Nhà máy', readonly=True)
    type_id = fields.Many2one('multi.approval.type', string='Loại phiếu', readonly=True)
    line_id = fields.Many2one('multi.approval.line', string='line', readonly=True)
    user_approve = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    # deadline = fields.Date(string='Ngày đến hạn', readonly=True)
    # priority = fields.priority = fields.Selection(
    #     [('0', 'Normal'),
    #     ('1', 'Medium'),
    #     ('2', 'High'),
    #     ('3', 'Very High')], string='Ưu tiên', default=0, readonly=True)
    time_out = fields.Datetime(string='Thời gian ra', readonly=True)
    time_in = fields.Datetime(string='Thời gian vào', readonly=True)


    def _select(self):
        return """
            SELECT row_number() OVER () as id, l.code, l.name, l.description, l.request_date
                    , l.date_start, l.date_end, l.reason_wl, l.state, emp.description as mnv
                    , l.user_id, emp.nhamaywl
                    , l.type_id as type_id, l.line_id, line.user_id as pic_id
                    , line.deadline, l.priority, l.time_out, l.time_in
        """
    def _from(self):
        return """
            multi_approval as l
                left join res_users as r on l.user_id = r.id
                left join multi_approval_type as t on t.id = l.type_id
                left join multi_approval_line as line on line.id = l.line_id
                left join hr_employee as emp on emp.user_id = r.id
        """
    def _where(self):
        return """
            t.id = 1 and l.state != 'Draft'
        """
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'report_multi_approval_ra_cong')
        self.env.cr.execute("""CREATE or REPLACE VIEW report_multi_approval_ra_cong as (
            select row_number() OVER () as id, * from report_ra_cong()
            );""" )