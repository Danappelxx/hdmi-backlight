#include "Particle.h"
#include "SerialBufferRK.h"
#include <FastLED.h>

using namespace NSFastLED;

#define DATA_PIN    D0
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define NUM_LEDS    100 //150 total, 50 cut off
CRGB leds[NUM_LEDS];
SerialBuffer<4096> serBuf(Serial1);

SYSTEM_THREAD(ENABLED);

int setBrightness(String input) {
    // input: (0,100)
    long brightness = input.toInt();
    brightness = (long)(((float)brightness / 100) * (float)255);
    FastLED.setBrightness(brightness);
    return brightness;
}

void setup() {
    Particle.function("setBrightness", setBrightness);

    Serial1.begin(115200);
    serBuf.setup();

    // tell FastLED about the LED strip configuration
    FastLED.addLeds<LED_TYPE,DATA_PIN,COLOR_ORDER>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);

    FastLED.show();
}

CRGB readColor() {
    CRGB color;
    color.red = (uint8_t) serBuf.read();
    color.green = (uint8_t) serBuf.read();
    color.blue = (uint8_t) serBuf.read();
    return color;
}

void loop() {
    if (serBuf.available() >= (2 + 4*3)) {
        if (serBuf.read() != 52 || serBuf.read() != 25) {
            return;
        }

        CRGB upper_left = readColor(); // 66-91
        CRGB upper_right = readColor(); // 41-66
        CRGB lower_left = readColor(); // 0-16, 91-100
        CRGB lower_right = readColor(); // 16-41

        for (int i = 0; i < 100; i++) {
            CRGB color;
            if (i < 16) {
                color = lower_left;
            } else if (i < 41) {
                color = lower_right;
            } else if (i < 66) {
                color = upper_right;
            } else if (i < 91) {
                color = upper_left;
            } else {
                color = lower_left;
            }
            leds[i] = color;
        }

        FastLED.show();
    }
}
