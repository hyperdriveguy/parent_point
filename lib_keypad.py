from RPi import GPIO
from time import sleep

# Constants

# Keypad layout
KEYS = (('1', '2', '3', 'A'),
        ('4', '5', '6', 'B'),
        ('7', '8', '9', 'C'),
        ('*', '0', '#', 'D'))

# Used GPIOs (pin numbers)
COL = (7, 11, 13, 15)
ROW = (12, 16, 18, 22)


def keypad_setup():
    GPIO.setmode(GPIO.BOARD)

    for col_index in range(4):
        GPIO.setup(COL[col_index], GPIO.OUT)
        GPIO.output(COL[col_index], 1)

    for row_index in range(4):
        GPIO.setup(ROW[row_index], GPIO.IN, pull_up_down=GPIO.PUD_UP)


def poll_keypad(poll_delay=0.1):
    while True:
        for column_index in range(4):
            GPIO.output(COL[column_index], 0)

            for row_index in range(4):
                if GPIO.input(ROW[row_index]) == 0:
                    while GPIO.input(ROW[row_index]) == 0:
                        sleep(poll_delay/10)
                    return KEYS[column_index][row_index]

            GPIO.output(COL[column_index], 1)
        sleep(poll_delay)


def get_key_seq(seq_length=1, delay=0.1):
    if seq_length == 0:
        raise ValueError('Cannot poll keypad for a sequence length of zero.')
    pressed_keys = []
    try:
        while(seq_length > len(pressed_keys)):
            key = poll_keypad(delay)
            pressed_keys.append(key)
        return pressed_keys

    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == '__main__':
    keypad_setup()
    print(get_key_seq(4))
    GPIO.cleanup()
