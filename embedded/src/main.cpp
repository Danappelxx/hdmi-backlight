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

int getBrightness() {
    return (long)((float)100 * ((float)FastLED.getBrightness() / 255)) / 5 * 5;
}

void setup() {
    Particle.function("setBrightness", setBrightness);
    Particle.variable("brightness", getBrightness);

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

        // top & bottom strips are 32 pixels, left & right are 18
        // bottom strip: 0-32 (0-10, 10-22, 22-32)
        // right strip: 32-50 (32-41, 41-50)
        // top strip: 50-82 (50-60, 60-72, 72-82)
        // left strip: 82-100 (82-91, 91-100)

        CRGB upper_left = readColor(); // 72-82, 82-91 (19)
        CRGB upper_middle = readColor(); // 60-72 (12)
        CRGB upper_right = readColor(); //  41-50, 50-60 (19)
        CRGB lower_left = readColor(); // 0-10, 91-100 (19)
        CRGB lower_middle = readColor(); // 10-22 (12)
        CRGB lower_right = readColor(); // 22-32, 32-41 (19)

        for (int i = 0; i < 100; i++) {
            CRGB color;
            if (i < 10) {
                color = lower_left; // 0-10
            } else if (i < 22) {
                color = lower_middle; // 10-22
            } else if (i < 41) {
                color = lower_right; // 22-41
            } else if (i < 60) {
                color = upper_right;  // 41-60
            } else if (i < 72) {
                color = upper_middle; // 60-72
            } else if (i < 91) {
                color = upper_left; // 72-91
            } else {
                color = lower_left; // 91-100
            }
            leds[i] = color;
        }

        FastLED.show();
    }
}
