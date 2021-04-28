from rpi_ws281x import PixelStrip, Color

# LED strip configuration:
LED_COUNT = 100        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

class DMALeds:
    def __init__(self):
        self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

    def start(self):
        self.strip.begin()

    def cleanup(self):
        self.strip._cleanup()

    def show(self, colors):
        colors = [Color(red=c[0], green=c[1], blue=c[2]) for c in colors]
        # colors: [upper_left, upper_middle, upper_right, lower_left, lower_middle, lower_right]
        upper_left, upper_middle, upper_right, lower_left, lower_middle, lower_right = colors

        for i in range(100):
            if i < 10:
                color = lower_left # 0-10
            elif i < 22:
                color = lower_middle # 10-22
            elif i < 41:
                color = lower_right # 22-41
            elif i < 60:
                color = upper_right  # 41-60
            elif i < 72:
                color = upper_middle # 60-72
            elif i < 91:
                color = upper_left # 72-91
            else:
                color = lower_left # 91-100
            self.strip.setPixelColor(i, color)

        self.strip.show()


if __name__ == "__main__":
    import time
    import random
    leds = DMALeds()
    colors = [
        [255,0,0], # upper_left
        [255,0,255], # upper_middle
        [0,0,255], # upper_right
        [0,255,255], # lower_left
        [0,255,0], # lower_middle
        [255,255,0], # lower_right
    ]

    while True:
        leds.show(colors)
        time.sleep(0.5)
        random.shuffle(colors)

