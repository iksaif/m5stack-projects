import os, sys, io
import M5
from M5 import *
from hardware import Timer, RGB
import time
from unit import RGBUnit
import random
import math

TIME_SCREEN_IDX = 0
TIMER_LIGHTSTRIP_IDX = 1
LEDS_COUNT = 28

class Calendar:
    def __init__(self, screen, leds):
        self.screen = screen
        self.leds = leds
        self.timer = Timer(TIME_SCREEN_IDX)
        self.lightstrip = LightStrip(self.leds, LEDS_COUNT)
        self.lightstrip_updater = None

    def setup(self):
        self.init_screen()
        self.timer.init(mode=Timer.PERIODIC, period=10000, callback=self.update)
        print("started")

    def stop(self):
        self.timer.deinit()
        if self.lightstrip_updater:
            self.lightstrip_updater.stop()

    def init_screen(self):
        self.screen.set_screen([0] * 24)
        self.change_lightstrip()
    
    def change_lightstrip(self):
        if self.lightstrip_updater:
            self.lightstrip_updater.stop()

        cls = random.choice([LightStripSimple, LightStripStars, LightStripRainbow, LightStripSnake])
        print("Changing to ", cls)
        lightstrip_updater = cls(self.lightstrip, TIMER_LIGHTSTRIP_IDX)
        print("go")
        lightstrip_updater.setup()
        self.lightstrip_updater = lightstrip_updater

    def update(self, timer):
        print("updated")
        self.update_screen(timer)
        self.change_lightstrip()

    def update_screen(self, timer):
        t = time.localtime()
        mday = t[2]
        month = t[1]
        if month < 12:
          mday = 0
          self.set_snow_on_screen()
        else:
            mday = min(mday, 25)
            if mday < 24:
                self.set_day_on_screen(mday)
            else:
                self.set_present_on_screen(mday)
    
    def set_day_on_screen(self, mday):
        screen = [0x00FF00] * mday + [0] * (24 - mday)
        self.screen.set_screen(screen)

    def set_snow_on_screen(self):
        """Set the screen to a snowflake pattern."""
        screen = [0] * 24
        for i in range(24):
            x = i % 6
            y = i // 6
            if x == 0 or x == 5 or y == 0 or y == 3:
                screen[i] = 0xFFFFFF
        self.screen.set_screen(screen)
    
    def set_present_on_screen(self, mday):
        """Set the screen to a present pattern."""
        screen = [0] * 24
        for i in range(24):
            x = i % 6
            y = i // 6
            if x == 0 or x == 5 or y == 0 or y == 3:
                screen[i] = 0xFFFFFF
        x = mday % 6
        y = mday // 6
        screen[mday] = 0xFF0000
        if x == 0 or x == 5 or y == 0 or y == 3:
            screen[mday] = 0xFFFFFF
        self.screen.set_screen(screen)

class LightStrip:
    def __init__(self, rgb, leds):
        self.rgb = rgb
        self.leds = [((0, 0, 0), 0, None)] * leds

    def num_leds(self):
        return len(self.leds)

    def get_led(self, led):
        return self.leds[led]

    def set_led(self, led, color, br, state):
        self.leds[led] = (color, br, state)

    def update(self):
        for led in range(self.num_leds()):
            color, br, state = self.get_led(led)
            (r, g, b) = color
            r = int(r * br / 100.)
            g = int(g * br / 100.)
            b = int(b * br / 100.)

            self.rgb.set_color(led, (r << 16 | g << 8 | b))

CHRISTMAS_COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "white": (255, 255, 255),
    "blue": (0, 0, 255),
    "purple": (128, 0, 128),
    "yellow": (255, 255, 0),
}


class LightStripSimple():
    HZ = 5

    def __init__(self, lightstrip, timeridx):
        self.lightstrip = lightstrip
        self.timer = Timer(timeridx)
        self.timer.init(period=1000 // self.HZ, mode=Timer.PERIODIC, callback=self.update)

    def setup(self):
        """Choose a random color for each LED."""
        for i in range(self.lightstrip.num_leds()):
            color = random.choice(list(CHRISTMAS_COLORS.values()))
            self.lightstrip.set_led(i, color, 100, True)

    def stop(self):
        self.timer.deinit()

    def update(self, timer):
        """Update the lightstrip.
        
        Move the colors of each LED one step to the right.
        """
        leds = self.lightstrip.num_leds()
        for i in range(leds - 1, 0, -1):
            color, br, state = self.lightstrip.get_led(i - 1)
            self.lightstrip.set_led(i, color, br, state)
        color = random.choice(list(CHRISTMAS_COLORS.values()))
        self.lightstrip.set_led(0, color, 100, True)
        self.lightstrip.update()

class LightStripStars():
    HZ = 5

    def __init__(self, lightstrip, timeridx):
        self.lightstrip = lightstrip
        self.timer = Timer(timeridx)
        self.timer.init(period=1000 // self.HZ, mode=Timer.PERIODIC, callback=self.update)

    def stop(self):
        self.timer.deinit()

    def setup(self):
        """All the LEDs are white or yellow."""
        for i in range(self.lightstrip.num_leds()):
            color = random.choice([CHRISTMAS_COLORS["white"], CHRISTMAS_COLORS["yellow"]])
            br = random.randint(0, 100)
            self.lightstrip.set_led(i, color, br, True)
    
    def update(self, timer):
        """Make the lights fade in and out."""
        leds = self.lightstrip.num_leds()
        for i in range(leds):
            color, br, state = self.lightstrip.get_led(i)
            if state:
                br = min(br + 10, 100)
                if br == 100:
                    state = False
            else:
                br = max(br - 10, 0)
                if br == 0:
                    state = True
            self.lightstrip.set_led(i, color, br, state)
        self.lightstrip.update()

class LightStripRainbow():
    HZ = 5

    def __init__(self, lightstrip, timeridx):
        self.lightstrip = lightstrip
        self.timer = Timer(timeridx)
        self.timer.init(period=1000 // self.HZ, mode=Timer.PERIODIC, callback=self.update)

    def stop(self):
        self.timer.deinit()

    def setup(self):
        """Set all LEDs to a random color."""
        for i in range(self.lightstrip.num_leds()):
            color = random.choice(list(CHRISTMAS_COLORS.values()))
            br = random.randint(0, 100)
            self.lightstrip.set_led(i, color, br, True)

    def update(self, timer):
        """Rotate the colors of the LEDs."""
        leds = self.lightstrip.num_leds()
        for i in range(leds - 1, 0, -1):
            color, br, state = self.lightstrip.get_led(i - 1)
            self.lightstrip.set_led(i, color, br, state)
        color = random.choice(list(CHRISTMAS_COLORS.values()))
        br = random.randint(0, 100)
        self.lightstrip.set_led(0, color, br, True)
        self.lightstrip.update()


class LightStripSnake():
    HZ = 5

    def __init__(self, lightstrip, timeridx):
        self.lightstrip = lightstrip
        self.timer = Timer(timeridx)
        self.timer.init(period=1000 // self.HZ, mode=Timer.PERIODIC, callback=self.update)

    def stop(self):
        self.timer.deinit()

    def setup(self):
        """Set all LEDs to a random color."""
        for i in range(self.lightstrip.num_leds()):
            color = random.choice(list(CHRISTMAS_COLORS.values()))
            br = random.randint(0, 100)
            self.lightstrip.set_led(i, color, br, True)

    def update(self, timer):
        """Move the colors of the LEDs one step to the right."""
        leds = self.lightstrip.num_leds()
        color, br, state = self.lightstrip.get_led(leds - 1)
        for i in range(leds - 1, 0, -1):
            color, br, state = self.lightstrip.get_led(i - 1)
            self.lightstrip.set_led(i, color, br, state)
        color = random.choice(list(CHRISTMAS_COLORS.values()))
        br = random.randint(0, 100)
        self.lightstrip.set_led(0, color, br, True)
        self.lightstrip.update()


calendar = None

def setup():
    global calendar

    print("setup")
    M5.begin()

    screen = RGB()
    leds = RGBUnit((32, 26), LEDS_COUNT)

    calendar = Calendar(screen, leds)
    calendar.setup()


def loop():
    M5.update()
    time.sleep_ms(100)


if __name__ == "__main__":
    try:
        setup()
        while True:
            loop()
    except (Exception, KeyboardInterrupt) as e:
        try:
            from utility import print_error_msg

            print_error_msg(e)
            try:
                calendar.stop()
            except Exception as e2:
                print(e2)
        except ImportError:
            print("please update to latest firmware")
