# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import logging
import re
import socket
import urllib.parse
import base64
from Crypto.Cipher import AES
from odoo.tools import config

_logger = logging.getLogger(__name__)

SECRET_KEY = (config.get('secret_key') or 'default_secret_key_32_bytes_long!').encode() if isinstance(config.get('secret_key') or 'default_secret_key_32_bytes_long!', str) else (config.get('secret_key') or b'default_secret_key_32_bytes_long!')

# Timeouts (seconds)
PORT_SCAN_TIMEOUT = 2.0
RTSP_PROBE_TIMEOUT = 4.0


def pscan(target, port, timeout=PORT_SCAN_TIMEOUT):
    """Return True if a TCP connection to target:port succeeds."""
    _logger.info("Executing pscan...")
    try:
        with socket.create_connection((target, int(port)), timeout=timeout):
            return True
    except Exception as e:
        _logger.warning("Error While Connection (%s:%s): %s", target, port, e)
        return False


def rtsp_probe(ip, port, timeout=RTSP_PROBE_TIMEOUT):
    """
    Send an RTSP OPTIONS request over a plain socket (no credentials sent).

    Returns (status, detail):
      - 'online'  : the port answered with an RTSP/1.0 reply (200 or 401 both count)
      - 'offline' : timeout, refused, or the port does not speak RTSP (e.g. HTTP)
    """
    try:
        with socket.create_connection((ip, int(port)), timeout=timeout) as s:
            s.settimeout(timeout)
            req = (
                f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\n"
                "CSeq: 1\r\n"
                "User-Agent: odoo-rtsp-probe\r\n\r\n"
            )
            s.sendall(req.encode())
            data = s.recv(1024).decode(errors='ignore')
    except socket.timeout:
        return 'offline', 'timeout'
    except (OSError, ValueError) as e:
        return 'offline', str(e)

    first_line = data.split('\r\n', 1)[0].strip()
    if first_line.startswith('RTSP/1.0'):
        return 'online', first_line
    return 'offline', f'Not RTSP: {first_line or "no response"}'


def mask_url(url):
    """Hide the password in rtsp://user:pass@host so it never reaches the logs."""
    if not url:
        return url
    return re.sub(r'(://[^:/@]+:)[^@]*(@)', r'\1****\2', url)


class AcArsIpCamera(models.Model):
    _name = 'ac.ars.ip.camera'
    _inherit = 'mail.thread'
    _description = 'ARS IP Camera'
    _rec_name = 'cam_name'

    cam_name = fields.Char(string="Camera Name")
    cam_brand = fields.Many2one('ac.ars.camera.config', string="Brand")
    user_name = fields.Char("User Name", tracking=True)
    password = fields.Char("Password", tracking=True)
    name = fields.Char("IP Address", tracking=True)
    local_ip = fields.Char("Local IP Address", tracking=True)
    http_port = fields.Char("HTTP Port")
    rstp_port = fields.Char("RSTP Port")
    company_id = fields.Many2one('res.company', "Company")
    rtsp_url = fields.Text("RTSP URL")
    main_stream = fields.Boolean()
    sub_stream = fields.Boolean()

    status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('unknown', 'Unknown'),
        ('progress', 'In Progress'),
        ('exception', 'Exception')
    ], string="Status", compute='_compute_status', store=False)

    ping_status = fields.Selection(related='status', string="Ping Status")

    recording = fields.Boolean()

    rtsp_status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('unknown', 'Unknown'),
        ('progress', 'In Progress'),
        ('exception', 'Exception')
    ], compute='_compute_status', store=False)

    dir_name = fields.Char("Directory Name")
    exception = fields.Text("Error Exceptions", compute='_compute_status', store=False)

    # Kept as Integer so this module stays independent of the module
    # that owns `live.streaming.settings`.
    server_id = fields.Integer(string="Server Settings ID")

    server_location = fields.Char("Server Location")
    record_stream_file = fields.Char("File name")
    reel_time = fields.Char("Reels Time")

    ip_camera_exp_ids = fields.One2many('ac.ars.ip.camera.exp', 'ip_cam_id', string="Expirations")

    # ------------------------------------------------------------------
    # Encryption helpers
    # ------------------------------------------------------------------
    def _encrypt_password(self, password):
        if not password:
            return password
        cipher = AES.new(SECRET_KEY, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(password.encode())
        encrypted = cipher.nonce + tag + ciphertext
        return base64.b64encode(encrypted).decode()

    def _decrypt_password(self, enc_password):
        if not enc_password:
            return enc_password
        try:
            data = base64.b64decode(enc_password)
            nonce = data[:16]
            tag = data[16:32]
            ciphertext = data[32:]

            cipher = AES.new(SECRET_KEY, AES.MODE_EAX, nonce=nonce)
            password = cipher.decrypt_and_verify(ciphertext, tag)
            return password.decode()
        except Exception:
            return enc_password

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            for f in ['password', 'user_name', 'name', 'local_ip']:
                if vals.get(f):
                    vals[f] = self._encrypt_password(vals[f])
        return super(AcArsIpCamera, self).create(vals_list)

    def write(self, vals):
        sensitive_fields = ['user_name', 'password', 'name', 'local_ip']
        for field in sensitive_fields:
            if vals.get(field) == '*********':
                vals.pop(field)
            elif vals.get(field):
                vals[field] = self._encrypt_password(vals[field])
        return super(AcArsIpCamera, self).write(vals)

    def read(self, fields=None, load='_classic_read'):
        """ Override read to mask credentials for non-admins """
        res = super(AcArsIpCamera, self).read(fields=fields, load=load)

        is_admin = self.env.user.has_group('ac_ars_cc_camera.live_stream_group_manager') or self.env.user.has_group('base.group_system')

        for record in res:
            for f in ['user_name', 'password', 'name', 'local_ip']:
                if f in record and record[f]:
                    if not is_admin:
                        record[f] = '*********'
                    else:
                        record[f] = self._decrypt_password(record[f])

        return res

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange('main_stream', 'sub_stream')
    def stream_change(self):
        _logger.info("Executing stream_change...")
        self.status = False
        if self.main_stream:
            self.sub_stream = False
        if self.sub_stream:
            self.main_stream = False

    @api.onchange('cam_brand', 'name')
    def _get_default_url(self):
        _logger.info("Executing _get_default_url...")
        if self.cam_brand:
            self.rtsp_url = self.cam_brand.rtsp_url
            self.local_ip = self.name

    # ------------------------------------------------------------------
    # Status checks
    # ------------------------------------------------------------------
    def _update_camera_offline_status(self, ip_address, port):
        _logger.info("Executing _update_camera_offline_status...")
        if not pscan(ip_address, port):
            today = fields.Date.today()
            self.status = 'offline'
            ss_obj = self.env['ac.ars.ip.camera.exp'].sudo().search(
                [('ip_cam_id', '=', self.id), ('port_status', '=', 'offline')], order='id desc', limit=1)
            if ss_obj:
                ss_obj.camera_expiry_update()
            else:
                now = datetime.now()
                vals = {
                    'ip_cam_id': self.id,
                    'name': now.strftime("%A"),
                    'port_status': 'offline',
                    'email_send_date': today,
                    'offline_datetime': fields.Datetime.now()
                }
                self.env['ac.ars.ip.camera.exp'].create(vals)
        else:
            self.status = 'online'

    @api.depends('rtsp_url', 'main_stream', 'sub_stream', 'name', 'http_port', 'rstp_port')
    def _compute_status(self):
        _logger.info("Executing _compute_status...")
        for res in self:
            ip = res._decrypt_password(res.name) if res.name else False
            rtsp_port = res.rstp_port or res.http_port
            ping_port = res.http_port or res.rstp_port
            error_msgs = []

            # 1. Port (ping) check
            if ip and ping_port:
                try:
                    res.sudo()._update_camera_offline_status(ip, ping_port)
                except Exception as e:
                    _logger.error(f"Error While checking status: {e}")
                    res.status = 'exception'
                    error_msgs.append(f"Ping Error: {e}")
            else:
                res.status = False

            # 2. RTSP check (lightweight socket probe, no OpenCV).
            # Only for a single record (form view) to keep list views fast.
            if len(self) == 1 and ip and rtsp_port:
                try:
                    status, detail = rtsp_probe(ip, rtsp_port)
                    _logger.info("RTSP probe %s:%s -> %s (%s)", ip, rtsp_port, status, detail)
                    res.rtsp_status = status
                    if status != 'online':
                        error_msgs.append(f"RTSP Probe Detail: {detail}")
                except Exception as e:
                    _logger.error(f"RTSP probe error: {e}")
                    res.rtsp_status = 'exception'
                    error_msgs.append(f"RTSP Error: {e}")
            else:
                res.rtsp_status = False

            res.exception = "\n".join(error_msgs) if error_msgs else False

    # ------------------------------------------------------------------
    # RTSP URL / actions
    # ------------------------------------------------------------------
    def get_rtsp_url(self):
        _logger.info("Executing get_rtsp_url...")
        self = self.sudo()
        rtsp_url = False
        if self.rtsp_url:
            rtsp_url = self.rtsp_url
            if self.user_name:
                rtsp_url = rtsp_url.replace('{user}', self._decrypt_password(self.user_name))

            if self.password:
                decrypted_password = self._decrypt_password(self.password)
                # Encode special characters (e.g. '!' becomes '%21')
                safe_password = urllib.parse.quote(decrypted_password, safe='')
                rtsp_url = rtsp_url.replace('{password}', safe_password)

            if self.name:
                rtsp_url = rtsp_url.replace('{ipaddress}', self._decrypt_password(self.name))
            if self.rstp_port:
                rtsp_url = rtsp_url.replace('{port}', self.rstp_port)
            elif self.http_port:
                rtsp_url = rtsp_url.replace('{port}', self.http_port)
            if self.main_stream:
                rtsp_url = rtsp_url.replace('{streamtype}', '0')
            elif self.sub_stream:
                rtsp_url = rtsp_url.replace('{streamtype}', '1')
            # A URL can never contain whitespace. The template (Text field) often
            # has a trailing newline, which breaks the RTSP request line and makes
            # the camera silently ignore ffmpeg.
            rtsp_url = re.sub(r'\s+', '', rtsp_url)
        return rtsp_url

    def action_open_camera_stream(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'ac_ars_camera_stream',
            'target': 'new',
            'params': {
                'camera_id': self.id,
                'stream_url': self.rtsp_url,
                'title': self.cam_name,
            },
        }


class AcArsIpCameraExp(models.Model):
    _name = 'ac.ars.ip.camera.exp'
    _description = 'ARS IP Camera Expiry'

    name = fields.Char(string="Name")
    offline_datetime = fields.Datetime(string="Offline Datetime")
    duration = fields.Char(string="Duration")
    last_online = fields.Datetime(string="Last Online")
    day_diff = fields.Integer(string="Day Diff")
    send_mail = fields.Boolean(string="Send Mail")
    port_status = fields.Selection([('online', 'Became Online'), ('offline', 'Offline')])
    description = fields.Text("Description")
    email_send_date = fields.Date()
    ip_cam_id = fields.Many2one('ac.ars.ip.camera')

    def camera_expiry_update(self):
        _logger.info("Executing camera_expiry_update...")
        current_dt = fields.Datetime.now()
        if self.offline_datetime:
            date_count = current_dt - self.offline_datetime
            self.write({'duration': str(date_count)})
            return True