import serial

def read_response_as_lines(ser):
    """
    :param ser: The serial port that is connected (an open) to the NanoVNA
    :return: An array of strings, one for each line returned
    """
    # The ch> prompt is used as the delimiter
    data = ser.read_until(b'ch> ')
    # Pull off the last part (not relevant data)
    data = data[:-4]
    # Break into lines and then decode into strings.
    return [line.decode("utf-8") for line in data.splitlines()]

def run_command(ser, command):
    """
    :param ser: The serial port that is connected (an open) to the NanoVNA
    :param command: The command to send
    :return: An array of strings, one for each line returned by the command
    """
    ser.write((command + "\r").encode("utf-8"))
    lines = read_response_as_lines(ser)
    # We discard the first line because that is the echo of the command
    return lines[1:]

# Open the serial port to the NanoVNA
ser = serial.Serial('/dev/cu.usbmodem4001')

lines = run_command(ser,"info")
print(lines)
