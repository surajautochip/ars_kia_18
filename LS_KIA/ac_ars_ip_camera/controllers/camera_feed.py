# -*- coding: utf-8 -*-
"""
Direct camera feed served by Odoo itself (no FastAPI server, no register step).

Browsers cannot play RTSP, so this controller runs ffmpeg, converts the RTSP
stream to MJPEG and streams it as multipart/x-mixed-replace. The widget just
puts the URL in an <img> tag.

Route: /ac_ars_ip_camera/video_feed/<camera_id>?quality=low|medium|high&fps=15

ffmpeg lookup order:
  1. System parameter  ac_ars_ip_camera.ffmpeg_path  (Settings > Technical > Parameters)
  2. `ffmpeg` on PATH
  3. FFMPEG_FALLBACK below
"""
import logging
import re
import shutil
import subprocess
import threading
from collections import deque

from werkzeug.wrappers import Response

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

FFMPEG_FALLBACK = r"C:\Users\saiki\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
FIRST_FRAME_TIMEOUT = 15  # seconds to wait for the first frame before giving up

SOI = b"\xff\xd8"  # JPEG start of image
EOI = b"\xff\xd9"  # JPEG end of image

QUALITY_FILTERS = {
    "high": [],
    "medium": ["-vf", "scale=1280:-2"],
    "low": ["-vf", "scale=640:-2"],
}


def _mask(text):
    """Hide the password in rtsp://user:pass@host"""
    return re.sub(r"(://[^:/@\s]+:)[^@\s]*(@)", r"\1****\2", text or "")


def _mjpeg_frames(proc):
    """Split ffmpeg's raw MJPEG stdout into individual JPEG frames."""
    buf = b""
    while True:
        chunk = proc.stdout.read(65536)
        if not chunk:
            break
        buf += chunk
        while True:
            start = buf.find(SOI)
            if start == -1:
                buf = buf[-1:]  # keep 1 byte in case the marker is split
                break
            end = buf.find(EOI, start + 2)
            if end == -1:
                buf = buf[start:]
                break
            yield buf[start:end + 2]
            buf = buf[end + 2:]


def _kill(proc):
    try:
        proc.kill()
        proc.wait(timeout=2)
    except Exception:
        pass


def _start_ffmpeg(cmd):
    """Start ffmpeg; return (process, stderr_tail, drain_thread)."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        bufsize=0,
    )
    tail = deque(maxlen=40)

    def drain():
        # Keeps the stderr pipe from filling up and remembers the last lines
        for line in iter(proc.stderr.readline, b""):
            tail.append(_mask(line.decode(errors="ignore").strip()))

    thread = threading.Thread(target=drain, daemon=True)
    thread.start()
    return proc, tail, thread


def _part(frame):
    return (
        b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
        + str(len(frame)).encode()
        + b"\r\n\r\n"
        + frame
        + b"\r\n"
    )


def _stream(proc, frames, first_frame, cam_id):
    try:
        yield _part(first_frame)
        for frame in frames:
            yield _part(frame)
    finally:
        # Runs when the browser closes the dialog / drops the connection
        _kill(proc)
        _logger.info("Camera %s: ffmpeg stopped", cam_id)


class CameraFeed(http.Controller):

    @http.route("/ac_ars_ip_camera/video_feed/<int:camera_id>", type="http", auth="user")
    def video_feed(self, camera_id, quality="medium", fps=15, **kw):
        # Do all ORM work BEFORE streaming: the DB cursor is closed once this
        # method returns, so the generator must not touch `request.env`.
        camera = request.env["ac.ars.ip.camera"].browse(camera_id).exists()
        if not camera:
            return request.not_found()
        camera.check_access("read")

        rtsp_url = "".join((camera.get_rtsp_url() or "").split())
        if not rtsp_url:
            return Response("No RTSP URL configured for this camera", status=400)

        ffmpeg = (
            request.env["ir.config_parameter"].sudo().get_param("ac_ars_ip_camera.ffmpeg_path")
            or shutil.which("ffmpeg")
            or FFMPEG_FALLBACK
        )

        try:
            fps = max(1, min(int(fps), 30))
        except (TypeError, ValueError):
            fps = 15

        # Same shape as the command that worked in the terminal, plus MJPEG output.
        cmd = [
            ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel", "verbose",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-an",
            "-r", str(fps),
            *QUALITY_FILTERS.get(quality, QUALITY_FILTERS["medium"]),
            "-q:v", "5",
            "-f", "mjpeg",
            "-",
        ]
        _logger.info("Camera %s: opening feed %s using %s", camera_id, _mask(rtsp_url), ffmpeg)

        try:
            proc, tail, drain_thread = _start_ffmpeg(cmd)
        except OSError as e:
            _logger.error("Camera %s: cannot start ffmpeg (%s): %s", camera_id, ffmpeg, e)
            return Response(f"Cannot start ffmpeg at '{ffmpeg}': {e}", status=500)

        # Wait for the first frame; kill ffmpeg if the camera stays silent.
        frames = _mjpeg_frames(proc)
        watchdog = threading.Timer(FIRST_FRAME_TIMEOUT, proc.kill)
        watchdog.start()
        try:
            first_frame = next(frames, None)
        finally:
            watchdog.cancel()

        if first_frame is None:
            _kill(proc)
            drain_thread.join(timeout=1)
            detail = "\n".join(tail)
            _logger.warning("Camera %s: no video received. ffmpeg said:\n%s", camera_id, detail)
            return Response(
                "Camera did not return video.\n" + detail,
                status=502,
                mimetype="text/plain",
            )

        _logger.info("Camera %s: first frame received, streaming", camera_id)
        return Response(
            _stream(proc, frames, first_frame, camera_id),
            mimetype="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
            direct_passthrough=True,
        )