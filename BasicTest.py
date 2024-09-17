import serial
import time
import pyautogui
port = serial.Serial(port='COM13', baudrate=115200, timeout=1)

while True:
    try:
        data = port.readall()
        if data:
            print(f"Received: {''.join(' ' + hex(letter)[2:] for letter in data)}")
            ascii_data = data.decode('ascii')
            ascii_data = ascii_data.replace('\x04', '{EOT}')
            ascii_data = ascii_data.replace('\x1E', '{RS}')
            ascii_data = ascii_data.replace('\x1D', '{GS}')
            print(ascii_data)
            pyautogui.write(ascii_data)
            time.sleep(0.1)
    except KeyboardInterrupt:
        port.close()
        break
