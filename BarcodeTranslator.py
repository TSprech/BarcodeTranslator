import re
import csv
import serial
import argparse
import logging
import pyautogui
from os import path
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.text import Text
from rich_argparse import RichHelpFormatter

if __name__ == '__main__':
    FORMAT = '%(message)s'
    logging.basicConfig(level='NOTSET', format=FORMAT, datefmt='[%X]', handlers=[RichHandler()])
    log = logging.getLogger('rich')

    console = Console()
    scan_number = 0


    def parse_arguments():
        parser = argparse.ArgumentParser(description='Replaces special characters from a barcode scanner', formatter_class=RichHelpFormatter)

        parser.add_argument('-p', '--port', type=str, required=True, help='Serial port the scanner is connected to as a string (e.g. COM3 or /dev/ttyUSB0)')
        parser.add_argument('-b', '--baud', type=int, required=True, default=115200, help='Baud rate as a number (e.g. 115200)')
        parser.add_argument('-k', '--key', type=str, required=True, default='Key.csv', help='File name as a string (e.g. Key.csv)')
        parser.add_argument('-x', '--hex', type=bool, required=False, default=False, help='Print the scanner data in hex (true) or decimal/ascii (false) (e.g. true)')

        args = parser.parse_args()
        return args


    def generate_replacement_dict(filename: str) -> dict:
        if path.isfile(filename):  # Make sure it is a file
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
        table = Table(title='Replacement Pairs', show_lines=True)  # Print out a table showing the replacement pairs for human verification
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


    def replace_and_color(input_string: str, replacements: dict, hex=False) -> (str, Text, Text):
        replaced_string = ''  # This will hold the string that is typed out
        original_text = Text()  # This is the rich string which will show what needs to be replaced in red
        replaced_text = Text()  # This is the rich string which will show what has been replaced in green
        for character in input_string:
            if character in replacements:  # If a replacement needs to be made
                replaced_string += replacements[character]  # First append the replacement into the typed string
                # If it is decimal/ascii format, just print the character's decimal value, if it is hex, convert each character to hex and print it TODO: Adjust to handle multichar replacement keys
                original_text.append(f'|{str(ord(character))}|' if not hex else f'|{" ".join(f"{ord(char):02X}" for char in character)}|', style="red")
                # Do the same with the replaced text string but in green
                replaced_text.append(replacements[character] if not hex else f'{" ".join(f"{ord(char):02X}" for char in replacements[character])}', style="green")
            else:
                replaced_string += character  # No replacement needed so just append it
                # For each of the rich strings just append the character in white to indicate it is not changed, in hex or ascii format depending on setting
                original_text.append(character if not hex else f'{" ".join(f"{ord(char):02X}" for char in character)}', style="white")
                replaced_text.append(character if not hex else f'{" ".join(f"{ord(char):02X}" for char in character)}', style="white")
            if hex:
                # Hex needs spaces between each to be legible
                original_text.append(' ')
                replaced_text.append(' ')
        return replaced_string, original_text, replaced_text


    args = parse_arguments()  # Parse command line arguments
    port = serial.Serial(port=args.port, baudrate=args.baud, timeout=0.5)  # Connect to the scanner
    replacement_dict = generate_replacement_dict(args.key)  # Generate the key replacement look up dictionary
    print_replacement_dict(replacement_dict)  # Print the table that shows what is replacing what

    while True:
        try:
            scanner_data = port.readall()  # Read everything from the scanner
            if scanner_data:
                scan_number += 1
                replaced, red, green = replace_and_color(scanner_data.decode('ascii'), replacement_dict, hex=args.hex)  # Generate the replaced string and the rich strings
                pyautogui.write(replaced)  # Type out the replaced string using emulated key presses
                table = Table(title=f'New Scan [b]#{scan_number}[/b] {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')  # Generate a title with a time stamp for a table showing the original and replaced strings
                table.add_column(f"[b]Original[/b]\tText to be replaced is marked in [red]red[/red] with the format: [red]|<{'hex' if args.hex else 'dec'} value>|[/red]", overflow='fold')
                table.add_column("[b]Replaced[/b]\tText that has been replaced is marked in [green]green[/green]", overflow='fold')  # Set to fold overflow to have it wrap instead of ellipses
                table.add_row(red, green)
                console.print(table)
        except KeyboardInterrupt:
            console.print(f"Shutting down translator, translated {scan_number} scans")
            port.close()
            break
