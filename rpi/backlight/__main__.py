from video_backlight import get_leds as get_video_leds, run as video_run, cleanup as video_cleanup
from audio_backlight import get_leds as get_audio_leds, run as audio_run

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json
import cgi

import sys
import time
import signal
import ctypes


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, manager):
        self.manager = manager

    def __call__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):

        if self.path == "/brightness":
            body = {
                "brightness": self.manager.get_brightness()
            }
            self.send_response(200)
        elif self.path == "/state":
            body = {
                "state": self.manager.state
            }
            self.send_response(200)
        else:
            body = {
                "error": "Not found"
            }
            self.send_response(404)

        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_POST(self):

        ctype, pdict = cgi.parse_header(self.headers["content-type"])

        # refuse to receive non-json content
        if ctype != "application/json":
            self.send_response(415)
            self.end_headers()
            return

        # read message
        length = int(self.headers["content-length"])
        message = json.loads(self.rfile.read(length))

        if self.path == "/brightness":
            self.manager.set_brightness(message["brightness"])
        elif self.path == "/state":
            new_state = message["state"]
            if new_state == "VIDEO":
                self.manager.transition(BacklightManager.STATE_VIDEO)
            elif new_state == "AUDIO":
                self.manager.transition(BacklightManager.STATE_AUDIO)
            else:
                self.send_response(400)
                self.end_headers()
                return
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()

class BacklightManager:
    STATE_STOPPED = -1
    STATE_NONE = 0
    STATE_VIDEO = 1
    STATE_AUDIO = 2
    STATE_ERROR = 3
    STATE_CHANGING_AUDIO_TO_VIDEO = 4
    STATE_CHANGING_VIDEO_TO_AUDIO = 5

    def __init__(self):
        self.state = self.STATE_NONE
        self.brightness = 255
        self.stopped = False

    def _should_stop(self):
        return self.state == self.STATE_CHANGING_VIDEO_TO_AUDIO or self.state == self.STATE_CHANGING_AUDIO_TO_VIDEO or self.state == self.STATE_STOPPED

    def run(self):
        while True:
            print(f"state: {self.state}")
            if self.state == self.STATE_VIDEO:
                video_run(self._should_stop)
                if self.state == self.STATE_VIDEO:
                    # if no change in state, then we stopped because of an error
                    self.state = self.STATE_ERROR
            elif self.state == self.STATE_AUDIO:
                audio_run(self._should_stop)
                if self.state == self.STATE_AUDIO:
                    # if no change in state, then we stopped because of an error
                    self.state = self.STATE_ERROR
            elif self.state == self.STATE_CHANGING_VIDEO_TO_AUDIO:
                self.state = self.STATE_AUDIO
            elif self.state == self.STATE_CHANGING_AUDIO_TO_VIDEO:
                self.state = self.STATE_VIDEO
            else:
                # should never happen?
                print(f"UNEXPECTED STATE: {self.state}")
                break
        self.stopped = True
        print("BacklightManager broke loop")

    def transition(self, state):
        if self.state == state:
            pass
        elif self.state == self.STATE_VIDEO and state == self.STATE_AUDIO:
            print(f"transition VIDEO -> AUDIO")
            self.state = self.STATE_CHANGING_VIDEO_TO_AUDIO
        elif self.state == self.STATE_AUDIO and state == self.STATE_VIDEO:
            print(f"transition AUDIO -> VIDEO")
            self.state = self.STATE_CHANGING_AUDIO_TO_VIDEO
        self.set_brightness(self.brightness)

    def set_brightness(self, brightness):
        brightness = int(brightness)
        self.brightness = brightness
        if self.state == self.STATE_VIDEO:
            get_video_leds().set_brightness(brightness)
            return True
        elif self.state == self.STATE_AUDIO:
            get_audio_leds().setBrightness(brightness)
            return True
        else:
            return False

    def get_brightness(self):
        if self.state == self.STATE_VIDEO:
            return get_video_leds().get_brightness()
        elif self.state == self.STATE_AUDIO:
            return get_audio_leds().getBrightness()
        else:
            return None

def kill_thread(thread):
    thread_id = thread.ident
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print("Exception raise failure")

def signal_handler(signum, frame):
    # ignore additional signals
    signal.signal(signum, signal.SIG_IGN)

    if server_thread is not None:
        kill_thread(server_thread)

    if manager.state == BacklightManager.STATE_VIDEO:
        video_cleanup()

    sys.exit(0)

if __name__ == "__main__":
    # catch ctrl+c
    signal.signal(signal.SIGINT, signal_handler)
    # catch systemd stop
    signal.signal(signal.SIGTERM, signal_handler)

    manager = BacklightManager()

    server = HTTPServer(("0.0.0.0", 80), RequestHandler(manager))
    def serve():
        print("Starting http server on 0.0.0.0:80")
        server.serve_forever()

    server_thread = Thread(target=serve)
    server_thread.start()

    manager.state = BacklightManager.STATE_AUDIO
    manager.run()

    print("Killing server thread...")
    kill_thread(server_thread)
    print("Done")
