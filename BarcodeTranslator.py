import serial
import pyautogui
import csv
import re
from os import path
from rich.console import Console
import logging
from rich.logging import RichHandler
from rich.table import Table
import argparse

from rich.text import Text
from rich_argparse import RichHelpFormatter

FORMAT = '%(message)s'
logging.basicConfig(level='NOTSET', format=FORMAT, datefmt='[%X]', handlers=[RichHandler()])
log = logging.getLogger('rich')

console = Console()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Replaces special characters from a barcode scanner', formatter_class=RichHelpFormatter)

    parser.add_argument('-p', '--port',  type=str, required=True, help='Serial port the scanner is connected to as a string (e.g. COM3 or /dev/ttyUSB0)')
    parser.add_argument('-b', '--baud', type=int, required=True, default=115200, help='Baud rate as a number (e.g. 115200)')
    parser.add_argument('-k', '--key', type=str, required=True, default='Key.csv', help='File name as a string (e.g. Key.csv)')

    args = parser.parse_args()
    return args

def generate_replacement_dict(filename: str) -> dict:
    if path.isfile(filename):
        with open(filename) as csv_file:
            replacement_dict = {}
            reader = csv.reader(csv_file)
            for row in reader:  # Each row is a key replacement pair in key, replacement\n order
                if len(row) == 2:  # Make sure that the row length is exactly 2 to account for the key and replacement pair
                    number, string = int(row[0]), row[1]
                    if 0 < number < 255:  # Only works for ASCII characters for now
                        replacement_dict[chr(number)] = string  # Create a key which is the value to be replaced and a value which is what replaces it
            return replacement_dict
    else:
        log.error(f'File {filename} does not exist, exiting...')
        exit(1)

def print_replacement_dict(replacement_dict: dict) -> None:
    table = Table(title='Replacement Pairs', show_lines=True)
    table.add_column("ASCII")
    table.add_column("DEC")
    table.add_column("HEX")
    table.add_column("Replacement")

    for key, value in replacement_dict.items():
        table.add_row(key, str(ord(key)), hex(ord(key)).upper(), value)

    console.print(table)

def replace_numbers(input_string: str, replacements: dict) -> str:
    pattern = re.compile('|'.join(re.escape(key) for key in replacements.keys()))  # Create a regular expression pattern that matches any of the keys
    return pattern.sub(lambda match: replacements[match.group(0)], input_string)  # Use the pattern to replace all occurrences in one pass

def print_replaced_string(input_string: str, replacements: dict) -> str:
    text = Text()
    for character in input_string:
        if character in replacements:
            text.append(replacements[character], style="green")
        else:
            text.append(character, style="white")

    console.print(text)

def print_original_string(input_string: str, replacements: dict) -> str:
    text = Text()
    for character in input_string:
        if character in replacements:
            text.append('|', style="red")
            text.append(str(ord(character)), style="red")
            text.append('|', style="red")
        else:
            text.append(character, style="white")

    console.print(text)


def format_and_color_bytearray(byte_array, replacements):
    text = Text()

    for byte in byte_array:
        hex_value = f'{byte:02X}'
        if chr(byte) in replacements:
            text.append(hex_value, style="red")
        else:
            text.append(hex_value, style="white")
        text.append(" ")  # Add a space between hex values

    console.print(text)


def replace_and_color(input_string: str, replacements: dict, hex=False) -> (str, Text, Text):
    replaced_string = ''
    original_text = Text()
    replaced_text = Text()
    for character in input_string:
        if character in replacements:
            replaced_string += replacements[character]
            original_text.append(f'|{str(ord(character))}|' if not hex else f'|{ord(character):02X}|', style="red")
            replaced_text.append(replacements[character] if not hex else f'{replacements[character]:02X}', style="green")
        else:
            replaced_string += character
            original_text.append(character if not hex else f'{character:02X}', style="white")
            replaced_text.append(character if not hex else f'{character:02X}', style="white")
    return replaced_string, original_text, replaced_text


args = parse_arguments() # Parse command line arguments
port = serial.Serial(port=args.port, baudrate=args.baud, timeout=0.5) # Connect to the scanner
replacement_dict = generate_replacement_dict(args.key) # Generate the key replacement look up dictionary
print_replacement_dict(replacement_dict)


while True:
    try:
        scanner_data = port.readall()
        if scanner_data:
            # format_and_color_bytearray(scanner_data, replacement_dict)
            # replaced = replace_numbers(scanner_data.decode('ascii'), replacement_dict)
            replaced, red, green = replace_and_color(scanner_data.decode('ascii'), replacement_dict, hex=True)
            pyautogui.write(replaced)
            console.print(red)
            console.print(green)
            # print_original_string(scanner_data.decode('ascii'), replacement_dict)
            # print_replaced_string(scanner_data.decode('ascii'), replacement_dict)
            # log.info(f'Replaced: {replaced}')
    except KeyboardInterrupt:
        port.close()
        break


