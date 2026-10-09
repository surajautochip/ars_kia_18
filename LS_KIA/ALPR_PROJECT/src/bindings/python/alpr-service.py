import logging
_logger = logging.getLogger(__name__)

import urllib.request
import json
import requests
import base64
import threading
import pprint
from hikvisionapi import Client
from openalpr import Alpr
from argparse import ArgumentParser
import httplib2

ODOO_URL = "http://192.168.101.111:8079" # CHANGE THIS TO SERVER ODOO URL

parser = ArgumentParser(description='OpenALPR Python Test Program')

parser.add_argument("-c", "--country", dest="country", action="store", default="in",
                    help="License plate Country")

parser.add_argument("--config", dest="config", action="store", default="/etc/openalpr/openalpr.conf",
                    help="Path to openalpr.conf config file")

parser.add_argument("--runtime_data", dest="runtime_data", action="store", default="/usr/share/openalpr/runtime_data",
                    help="Path to OpenALPR runtime_data directory")

parser.add_argument('--plate_image', default="", help='License plate image file')

options = parser.parse_args()

payload = {"db": 'ARS',
           "user": 'admin', "password": 'autochip@505',
           "dealer_code": '', }
def call_online_api(cam_obj,encoded_string):
    _logger.info("Executing call_online_api...")
    _logger.info("ONLINE API")
    SECRET_KEY = cam_obj['req_type'][0]['token']
    url = 'https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=in&secret_key=%s' % (SECRET_KEY)
    r = requests.post(url, data=encoded_string)
    response = json.dumps(r.json())
    alpr_api_response = json.loads(response)
    _logger.info("Online API Final ",alpr_api_response)
    return alpr_api_response

def printit():
    _logger.info("Executing printit...")
    TIMEOUT = 20
    threading.Timer(20.0, printit).start()
    headers = {'Content-Type': 'application/json'}
    params = json.dumps(payload)
    url = ODOO_URL + "/ars_auto_lpr/get_camara_information"
    try:
        response = requests.request("POST", url, data=params, headers=headers, timeout=TIMEOUT)
        cameras_details = json.loads(response.text)
        camera_data = json.loads(cameras_details.get('result'))
        if camera_data:
            for cam_obj in camera_data.get('cameras'):
                alpr = None
                if len(cam_obj['camera_url']) < 5:
                    continue
                _logger.info(len(cam_obj['camera_url']))
                # cam = Client("http://" + cam_obj['camera_url'], cam_obj['username'], cam_obj['password'], timeout=30)
                # cam.count_events = 2  # The number of events we want to retrieve (default = 1)
                # response = cam.Streaming.channels[102].picture(method='get', type='opaque_data')
                # with open('screen.jpg', 'wb') as f:
                #     for chunk in response.iter_content(chunk_size=1024):
                #         if chunk:
                #             f.write(chunk)
                pic_url = ("http://" + cam_obj['camera_url'] + "/ISAPI/Streaming/channels/101/picture")
                # admin, Zebra01!
                h = httplib2.Http(".cache")
                h.add_credentials(cam_obj['username'], cam_obj['password'])  # Basic authentication
                resp, content = h.request(pic_url, "GET")
                with open('screen.jpg', 'wb') as f:
                    # for chunk in content.iter_content(chunk_size=1024):
                    #     if chunk:
                    f.write(content)
                with open("screen.jpg", "rb") as f:
                    data = f.read()
                    encoded_string = base64.b64encode(data)
                # Local Request
                alpr = Alpr(options.country, options.config, options.runtime_data)
                alpr.set_top_n(7)
                alpr.set_default_region("in")
                alpr.set_detect_region(False)
                # jpeg_bytes = open(options.plate_image, "rb").read()
                alpr_local_response = alpr.recognize_array(data)
                pprint.p_logger.info(alpr_local_response)
                if alpr_local_response['results'] != []:
                    for bay_obj in cam_obj['bays']:
                        if not bay_obj['is_bay_occupy']:
                            alpr_api_response = call_online_api(cam_obj,encoded_string)
                            bay_inside = False
                            for alpr_obj in alpr_api_response['results']:
                                alpr_x1 = alpr_obj['coordinates'][0]['x']
                                alpr_y1 = alpr_obj['coordinates'][0]['y']
                                alpr_x2 = alpr_obj['coordinates'][2]['x']
                                alpr_y2 = alpr_obj['coordinates'][2]['y']
                                if (alpr_x1 > bay_obj['x1'] * 2.42) and (alpr_y1 > bay_obj['y1'] * 2.42):
                                    if (alpr_x2 < bay_obj['x2'] * 2.42) and (alpr_y2 < bay_obj['y2'] * 2.42):
                                        _logger.info('in if')
                                        bay_inside = True
                                        num_plate = alpr_obj['plate']
                                        url = ODOO_URL + "/ars_auto_lpr/process_numplate_info"
                                        headers = {'Content-Type': 'application/json'}
                                        payload.update({
                                            "params": {
                                                'plate': num_plate,
                                                'bay_id': bay_obj['bay_id'],
                                                'cam_id': cam_obj['camera_id'],
                                                'type': 'in'
                                            }
                                        })
                                        data_json = json.dumps(payload)
                                        ctrl_req = requests.post(url=url, data=data_json, headers=headers)
                            # if bay_inside == False:
                            #     _logger.info('in else')
                            #     url = "http://192.168.1.38:8080/ars_auto_lpr/process_numplate_info?session_id=270032b50fd4f218dd387346130f2453c04bd9d8"
                            #     headers = {'Content-Type': 'application/json'}
                            #     data = {
                            #     "params":{
                            #         'plate' : "XXXX",
                            #         'bay_id' : bay_obj['bay_id'],
                            #         'cam_id' : cam_obj['camera_id'],
                            #         'type' : 'out'
                            #         }
                            #     }
                            #     data_json = json.dumps(data)
                            #     ctrl_req = requests.post(url=url, data=data_json, headers=headers)
                else:
                    for bay_obj in cam_obj['bays']:
                        if bay_obj['is_bay_occupy']:
                            url = ODOO_URL + "/ars_auto_lpr/alpr_bay_status"
                            payload.update({
                                'bay_id': bay_obj['bay_id'],
                                'cam_id': cam_obj['camera_id'],
                            })
                            params = json.dumps(payload)
                            try:
                                response = requests.request("POST", url, data=params, headers=headers, timeout=TIMEOUT)
                            except(ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema,
                                   requests.exceptions.Timeout, requests.exceptions.HTTPError) as error:
                                _logger.info(error)


    except (
            ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError)as error:
        status = 404
        message = error


printit()
