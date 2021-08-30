#!/usr/bin/env python3
import concurrent.futures as future
from time import sleep

import i2c_lcd_lib as lcd
import lib_keypad


def main():
    main_lcd = lcd.LCD()
    with future.ThreadPoolExecutor(2) as thread:
        r = thread.submit(main_lcd.display_rotating_text('Starting up APPM (Automated Parent Point Machine)'))
        r.result(5)
        print('Started')
