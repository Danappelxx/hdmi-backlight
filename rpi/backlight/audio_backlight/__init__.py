from . import visualization
from .led import get_leds, init_leds

def run(should_stop):
    # Initialize LEDs
    init_leds()
    visualization.led.update()
    # Start listening to live audio stream
    visualization.microphone.start_stream(should_stop, visualization.microphone_update)

if __name__ == "__main__":
    run()
