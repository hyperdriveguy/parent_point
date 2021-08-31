"""
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Refactored beyond recognition 2021 by Hyperdriveguy
Made available under GNU GENERAL PUBLIC LICENSE v3+

Original code found at:
https://gist.github.com/DenisFromHR/cc863375a6e19dce359d
"""

import smbus
from time import sleep

# Commands

LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# Flags for display entry mode

LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# Flags for display on/off control

LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# Flags for display/cursor shift

LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# Flags for function set

LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
# 2 Line mode should be used for 5v power, 1 line for 3.3v
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# Flags for backlight control

LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x02

# Enable bit
EN = 0x04
# Read/Write bit
RW = 0x02
# Register select bit
RS = 0x01


class LCD():

    # initializes objects and lcd

    def __init__(self,
                 num_lines=1,
                 line_length=16,
                 address=0x27,
                 port=0x01):
        """
        Initialize the I2C bus and write the initial LCD commands.

        The i2c bus/port should almost always be 0x01.
        If the default does not work, try a value of 0x00.

        The LCD address can be found when running 'i2cdetect -y 1'.
        The LCD address is likely to differ from the default listed.

        Args:
            num_lines (int, optional): number of lines to utilize in the LCD.
                Defaults to 1.
            line_length (int, optional):
                number of characters per line on the LCD. Defaults to 16.
            address (hexadecimal, optional): the I2C address of the LCD.
                Defaults to 0x27.
            port (hexadecimal, optional):
                port to be used for accessing the I2C bus. Defaults to 0x01.
        """

        self.address = address
        self.bus = smbus.SMBus(port)

        self.num_lines = num_lines
        self.line_length = line_length

        self.write_command(0x03)
        self.write_command(0x03)
        self.write_command(0x03)
        self.write_command(0x02)
        self.write_command(LCD_FUNCTIONSET | get_line_mode(num_lines) |
                           LCD_5x8DOTS | LCD_4BITMODE)

        self.write_command(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.write_command(LCD_CLEARDISPLAY)
        self.write_command(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        sleep(0.2)

    def write_i2c(self, cmd):
        """
        Write a byte directly to the I2C bus.

        Args:
            cmd (hexadecimal): byte to be written.
        """
        self.bus.write_byte(self.address, cmd)
        sleep(.0001)

    def strobe(self, data):
        """
        Use the enable bit to "latch" the command.
        TODO: This method needs more documentation.

        Args:
            data (hexadecimal): command nibble to be written.
        """
        self.write_i2c(data | EN | LCD_BACKLIGHT)
        sleep(.0005)
        self.write_i2c(data & ~EN | LCD_BACKLIGHT)
        sleep(.0001)

    def write_byte_nibble(self, data):
        """
        Writes byte nibbles in 4 bit mode.

        Args:
            data (hexadecimal): nibble passed from write_command.
        """
        self.write_i2c(data | LCD_BACKLIGHT)
        self.strobe(data)

    def write_command(self, cmd, mode=0x00):
        """
        Write byte command to the LCD.

        Args:
            cmd (hexadecimal): command byte to be written.
            mode (hexadecimal, optional): write mode. Defaults to 0x00.
        """
        self.write_byte_nibble(mode | cmd & 0xF0)
        self.write_byte_nibble(mode | cmd << 4 & 0xF0)

    def display_raw_string(self, string, line=1, pos=0):
        """
        Display a string to the LCD at a given position.

        Args:
            string (str): string to be written to the display.
            line (int, optional): line number to start displaying at.
                Defaults to 1.
            pos (hexadecimal, optional): position to start displaying at.
                Defaults to 0.
        """
        self.write_command(calc_pos_byte(line, pos))

        for char in string:
            self.write_command(ord(char), RS)

    def display_string(self, string, line=1, align='left', overflow='scroll'):
        if len(string) <= 0:
            self.clear_screen()
        elif len(string) <= self.line_length:
            padded_str = padd_str(string, self.line_length, align=align)
            self.display_raw_string(padded_str, line)
        else:
            if overflow == 'scroll':
                self.new_text_scroll(string, line)
                self.display_text_scroll(string)
                return True
            elif overflow == 'rotate':
                self.display_rotating_text(string, line)
            else:
                print('The following string was not displayed: ', string)
        return False

    def display_rotating_text(self, string, line=1, rate=0.5, timeout=10):
        # Double space notes end of rotation and increases readability
        line_overflow_buffer = string + '  '
        run_time = 0
        while True:
            str_subset = '<' + line_overflow_buffer[:self.line_length-2] + '>'
            self.display_raw_string(str_subset, line)
            line_overflow_buffer = rotate_string(line_overflow_buffer)
            sleep(rate)
            run_time += rate

    def new_text_scroll(self, string, line=1, begin='<', end='>'):
        self.scroll = ScrollingText(string, self.line_length, line, begin, end)

    def display_text_scroll(self):
        self.display_raw_string(self.scroll.get_cur_substring(), self.scroll.line)

    def scroll_text_forward(self, num_rotate=1):
        self.scroll.rotate_forward(num_rotate)
        self.display_raw_string(self.scroll.get_cur_substring(), self.scroll.line)

    def scroll_text_backward(self, num_rotate=1):
        self.scroll.rotate_backward(num_rotate)
        self.display_raw_string(self.scroll.get_cur_substring(), self.scroll.line)

    def clear_screen(self):
        """
        Clear the display and return cursor to home position.
        """
        self.write_command(LCD_CLEARDISPLAY)
        self.write_command(LCD_RETURNHOME)

    def backlight(self, light=True):
        """
        Turn the backlight on/off. Not supported by all LCDs.

        Args:
            light (bool, optional): determines the light should be on or off.
                Defaults to True.
        """
        if light:
            self.write_i2c(LCD_BACKLIGHT)
        else:
            self.write_i2c(LCD_NOBACKLIGHT)

    def load_custom_chars(self, fontdata):
        """
        Load custom characters into the LCD RAM.

        Args:
            fontdata (tuple): 2 dimensional tuple containing byte data for
                writing up to 8 custom characters.
        """
        self.write_command(LCD_SETCGRAMADDR)
        for char in fontdata:
            for line in char:
                self.write_command(line, 1)


class ScrollingText:

    def __init__(self, string, lcd_len, line=1, begin='<', end='>'):
        self.line = line

        self.overflow_buffer = string
        self.index_start = 0

        self.display_len = lcd_len - len(end)
        self.lcd_len = lcd_len

        self.scrollability = [False, True]
        self.begin = begin
        self.end = end

    def get_cur_substring(self):
        end_index = self.index_start + self.display_len
        sub_str = self.overflow_buffer[self.index_start:end_index]
        if self.scrollability[0]:
            sub_str = self.begin + sub_str
        if self.scrollability[1]:
            sub_str += self.end
        return sub_str

    def rotate_forward(self, num_rotate=1):
        projected_rotation = self.index_start + self.display_len + num_rotate
        if projected_rotation > len(self.overflow_buffer):
            raise IndexError('Cannot rotate past string end.')
        self.index_start += num_rotate
        self.mod_display_len()

    def rotate_backward(self, num_rotate=1):
        if self.index_start - num_rotate < 0:
            raise IndexError('Cannot rotate past string end.')
        self.index_start -= num_rotate
        self.mod_display_len()

    def mod_display_len(self):
        base_len = self.lcd_len
        if self.index_start > 0:
            base_len -= len(self.begin)
            self.scrollability[0] = True
        else:
            self.scrollability[0] = False
        if self.index_start + self.display_len < len(self.overflow_buffer):
            base_len -= len(self.end)
            self.scrollability[1] = True
        else:
            self.scrollability[1] = False
        self.display_len = base_len


def get_line_mode(lines):
    """
    Get the command depending on number of lines being used.

    Args:
        lines (int): total number of lines being used on the LCD.

    Raises:
        ValueError: the lines argument should never be zero or negative.

    Returns:
        hexadecimal: byte command to be written to the LCD.
    """
    if lines == 1:
        return LCD_1LINE
    if lines == 2:
        return LCD_2LINE
    else:
        raise ValueError('Line mode not handled by library.')


def calc_pos_byte(line, pos=0):
    """
    Get the byte to write for the line and position.

    Args:
        line (int): line number to set the position to.
        pos (int, optional): position in line to set the position to.
            Defaults to 0.

    Returns:
        hexadecimal: command to change the LCD position.
    """
    line_pos_bytes = (0x00, 0x40, 0x14, 0x54)
    return LCD_SETDDRAMADDR + line_pos_bytes[line - 1] + pos


def padd_str(string, full_len, pad_char=' ', align='left'):
    """
    Add padding to a string for alignment.

    Args:
        string (str): raw string.
        full_len (int): max length of the LCD or max length to pad.
        pad_char (str, optional): character used for padding. Defaults to ' '.
        align (str, optional): how to align the string.
            Valid values are 'left', 'center', and 'right'. Defaults to 'left'.

    Raises:
        IndexError: This happens if the given string is longer than the LCD.
        ValueError: Raised if the more than one character is given for padding.

    Returns:
        str: padded string to be written.
    """
    if len(string) == full_len:
        return string
    if len(string) > full_len:
        raise IndexError('String is too long')
    if len(pad_char) > 1:
        raise ValueError('Padding string must only contain one char')
    pad_length = full_len - len(string)
    if align == 'right':
        padded = (pad_char * pad_length) + string
        return padded
    if align == 'center':
        if pad_length % 2 == 1:
            pad_length = pad_length - 1
            string += ' '
        half_pad = pad_char * int(pad_length / 2)
        padded = half_pad + string + half_pad
        return padded
    else:
        padded = string + (pad_char * pad_length)
        return padded


def rotate_string(string, num_chars=1):
    to_end = string[:num_chars]
    to_begin = string[num_chars:]
    return to_begin + to_end


