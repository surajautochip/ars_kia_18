import logging
import requests
from odoo import http
from odoo.http import request
from odoo.tools import config

_logger = logging.getLogger(__name__)

SERVER_BASE_URL = config.get('live_streaming_base_url', "http://127.0.0.1:8888")

class LiveStreamingController(http.Controller):

    @http.route('/ac_ars_ip_camera/stream/url', type='json', auth='user')
    def get_stream_url(self):
        url = config.get('live_streaming_base_url', "http://127.0.0.1:8888")
        return {"url": url}

    @http.route('/ac_ars_ip_camera/register_stream', type='json', auth='user', methods=['POST'])
    def register_camera_stream(self, camera_id=None, **kwargs):
        """
        Register (start) a camera stream via the Flask microservice.
        Returns {'success': True} or {'success': False, 'error': '...'}
        """
        if not camera_id:
            _logger.warning("register_camera_stream called without camera_id")
            return {'success': False, 'error': 'No camera_id provided'}

        try:
            camera = request.env['ac.ars.ip.camera'].browse(int(camera_id))
            if not camera.exists():
                _logger.warning("register_camera_stream: camera with id=%s not found", camera_id)
                return {'success': False, 'error': 'Camera not found'}
            
            server_url = f"{SERVER_BASE_URL}/register_camera"
            payload = []
            for cam in camera:
                payload.append({
                    "camera_id": str(cam.id)+"_test",
                    "rtsp_url": cam.get_rtsp_url()
                })

            res = requests.post(server_url, json=payload, timeout=9)
            if res.status_code == 200:
                _logger.info("Camera stream registered successfully for camera_id=%s", camera_id)
                return {'success': True}
            if res.status_code == 202:
                _logger.info("Camera Already existed camera_id=%s", camera_id)
                return {'success': True}
            elif res.status_code == 401:
                _logger.error("register_camera_stream: Flask service returned error %s for camera_id=%s",
                              res.status_code, camera_id)
                return {'success': False, 'errorMsg': 'Camera was not connecting....'}
            else:
                _logger.error("register_camera_stream: Flask service returned error %s for camera_id=%s", res.status_code, camera_id)
                return {'success': False, 'error': 'Failed to register stream. Please check the streaming service.'}

        except Exception as e:
            _logger.exception("Unexpected error in register_camera_stream for camera_id=%s: %s", camera_id, e)
            return {'success': False, 'errorMsg': 'Server is not running start it.'}

    @http.route('/ac_ars_ip_camera/stop_stream', type='json', auth='user', methods=['POST'])
    def stop_camera_stream(self, camera_id=None, **kwargs):
        if not camera_id:
            _logger.warning("stop_camera_stream called without camera_id")
        try:
            server_url = f"{SERVER_BASE_URL}/stop_stream"
            payload = {
                "camera_id": [str(camera_id)+"_test"],
            }
            res = requests.post(server_url, json=payload, timeout=5)
            if res.status_code == 200:
                _logger.info("Camera stream Stoped successfully for camera_id=%s", camera_id)
                return {'status': True}
            else:
                _logger.error("stop_stream: Flask service returned error %s for camera_id=%s", res.status_code, camera_id)
                return {'status': False, 'error': 'Failed to register stream. Please check the streaming service.'}
        except Exception as e:
            _logger.exception("Unexpected error in stop_camera_stream for camera_id=%s: %s", camera_id, e)

    @http.route('/ac_ars_ip_camera/probe/<string:camera_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def probe_stream(self, camera_id, quality='medium', **kwargs):
        """
        Proxy route for bandwidth probing.
        Browser calls Odoo (same origin) → Odoo calls ls server internally → no CORS.
        Returns the raw JPEG frame + X-Stream-FPS header.
        """
        try:
            server_url = f"{SERVER_BASE_URL}/probe/{camera_id}?quality={quality}&_t={kwargs.get('_t', '')}"
            res = requests.get(server_url, timeout=5)

            if not res.ok:
                return request.make_response("No frame", status=503)

            response = request.make_response(
                res.content,
                headers=[
                    ('Content-Type', 'image/jpeg'),
                    ('Cache-Control', 'no-store, no-cache, must-revalidate'),
                    ('X-Stream-FPS', res.headers.get('X-Stream-FPS', '20')),
                ]
            )
            return response

        except Exception as e:
            _logger.exception("probe_stream error for camera_id=%s: %s", camera_id, e)
            return request.make_response("Probe failed", status=500)
