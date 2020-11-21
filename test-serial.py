import serial
import numpy as np
import pandas as pd

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

def get_complex_data(ser):
    lines = run_command(ser, "data")
    # Parse into real/imaginary tokens
    tokenized_lines = [line.split(" ") for line in lines]
    # Make into imaginary numbers
    return [complex(float(token[0]), float(token[1])) for token in tokenized_lines]


def reflection_coefficient_to_vswr(rc):
    """
    :param rc: A complex reflection coefficient
    :return: The scalar VSWR
    """
    gamma = abs(rc)
    return (1.0 + gamma) / (1.0 - gamma)


start_frequency = 28000000
end_frequency = 30000000
step_frequency = 250000
step_count = int((end_frequency - start_frequency) / step_frequency)
if start_frequency >= end_frequency or step_count > 50:
    raise Exception("Error")
print(step_count)

# Open the serial port to the NanoVNA
ser = serial.Serial('/dev/cu.usbmodem4001')

lines = run_command(ser,"info")
print("\n".join(lines))

run_command(ser,"sweep " + str(start_frequency) + " " + str(end_frequency))

lines = run_command(ser,"frequencies")
frequency_list = [float(line) for line in lines]
print(frequency_list)

# Make the VSWR data
rc_list = get_complex_data(ser)
print(rc_list)

vswr_list = [reflection_coefficient_to_vswr(rc) for rc in rc_list]
print(vswr_list)

# Load the VSWR data into a DataFrame indexed by the frequdency
df = pd.DataFrame(vswr_list, index=frequency_list)
print(df)
# Re-sample using the start/end/step provided by the user.  Linear
# interpolation is automatically used

df1 = df.reindex(np.linspace(start_frequency, end_frequency - step_frequency, step_count)).interpolate()
print(df1)