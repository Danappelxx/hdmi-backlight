from . import visualization
from .led import get_leds, init_leds


def run(lock):

    lock.acquire()

    # Initialize LEDs
    init_leds()
    visualization.led.update()
    # Start listening to live audio stream
    visualization.microphone.start_stream(lock, visualization.microphone_update)


if __name__ == "__main__":
    from ..backlight_lock import BacklightLock
    run()
