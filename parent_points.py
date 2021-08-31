#!/usr/bin/env python3
import concurrent.futures as future
from threading import main_thread
from time import sleep

import i2c_lcd_lib as lcd
import lib_keypad


def main():
    main_lcd = lcd.LCD()
    with future.ThreadPoolExecutor(2) as thread:
        r = thread.submit(main_lcd.display_rotating_text('Starting up APPM (Automated Parent Point Machine)', timeout=8))
        s = thread.submit(print('Yeet'))
        r.result(10)
        s.result()

        print('Started it')

main()
