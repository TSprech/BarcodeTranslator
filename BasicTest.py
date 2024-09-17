import serial
import pyautogui
import csv
port = serial.Serial(port='COM13', baudrate=115200, timeout=1)

# Convert CSV data to a dictionary
replacement_dict = {}
with open('Key.csv') as csv_data:
    for row in csv.reader(csv_data.readlines()):
        if len(row) == 2:
            number, string = row
            replacement_dict[chr(int(number))] = string

def replace_numbers(input_string: str, replacements: dict):
    for number, string in replacements.items():
        input_string = input_string.replace(number, string)
    return input_string


while True:
    try:
        new_character = port.readall()
        if new_character:
            print(f"Received: {''.join(' ' + hex(letter)[2:] for letter in new_character)}")
            ascii_character = new_character.decode('ascii')
            replaced = replace_numbers(ascii_character, replacement_dict)
            pyautogui.write(replaced)
            print(replaced)
    except KeyboardInterrupt:
        port.close()
        break


