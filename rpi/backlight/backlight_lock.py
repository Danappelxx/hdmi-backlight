from time import sleep
from threading import Lock


# Poor naming, but the idea is that audio/video modes call
# `should_release` on every iteration to see if its time for
# them to clean up. `should_release` returns True, then they
# perform whatever clean up is necessary and then call `release`.
# Once `release` has been called, the other mode can now acquire
# and send commands to the LEDs.
class BacklightLock:
    STATE_ACQUIRED = 1
    STATE_WAITING_FOR_RELEASE = 2
    STATE_RELEASED = 3

    def __init__(self):
        self.lock = Lock()
        self.state = BacklightLock.STATE_RELEASED

    def acquire(self):
        while True:
            with self.lock:
                if self.state == BacklightLock.STATE_RELEASED:
                    self.state = BacklightLock.STATE_ACQUIRED
                    break
            # TODO: do something less dumb
            sleep(0.05)

    def should_release(self):
        with self.lock:
            return self.state != BacklightLock.STATE_ACQUIRED

    def release(self):
        with self.lock:
            self.state = BacklightLock.STATE_RELEASED

    def wait_for_release(self):
        with self.lock:
            if self.state == BacklightLock.STATE_ACQUIRED:
                self.state = BacklightLock.STATE_WAITING_FOR_RELEASE
        while True:
            with self.lock:
                if self.state != BacklightLock.STATE_WAITING_FOR_RELEASE:
                    break
            # TODO: do something less dumb than this
            sleep(0.05)

    def wait_for_acquired(self):
        while True:
            with self.lock:
                if self.state == BacklightLock.STATE_ACQUIRED:
                    break
            sleep(0.05)
