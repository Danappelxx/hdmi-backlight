from . import visualization

def run():
    # Initialize LEDs
    visualization.led.update()
    # Start listening to live audio stream
    visualization.microphone.start_stream(visualization.microphone_update)

if __name__ == "__main__":
    run()
