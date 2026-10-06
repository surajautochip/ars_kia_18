# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.ac_rms.controllers.main import Home
import json
import urllib.parse
import werkzeug.utils
from datetime import datetime, timedelta
import werkzeug.utils
from odoo import http
from odoo.http import request
import pytz
from odoo import models, fields, api, _
import requests
import json
import base64

class Front_Home_Inherit(Home):
    # @http.route(['/tech_start'], type='json', auth="user", website=True, csrf=False)
    def calendar_event_insert(self, tasks, order_id, timesheet_ids, name):
        _logger.info("Executing calendar_event_insert...")
        res = super(Front_Home_Inherit, self).calendar_event_insert()

        return res
