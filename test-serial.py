import serial
import numpy as np
import pandas as pd
import nanovna as nv

start_frequency = 28000000
end_frequency = 30000000
step_frequency = 250000

step_count = int((end_frequency - start_frequency) / step_frequency)
if start_frequency >= end_frequency or step_count > 50:
    raise Exception("Error")

# Open the serial port to the NanoVNA
ser = serial.Serial('/dev/cu.usbmodem4001')

lines = nv.run_command(ser,"info")
print("\n".join(lines))

nv.run_command(ser, "sweep " + str(start_frequency) + " " + str(end_frequency))

lines = nv.run_command(ser, "frequencies")
frequency_list = [float(line) for line in lines]
print(frequency_list)
frequency_space = np.linspace(start_frequency, end_frequency - step_frequency, step_count)

# Make the VSWR data
rc_list = nv.get_complex_data(ser)
print(rc_list)

vswr_list = [nv.reflection_coefficient_to_vswr(rc) for rc in rc_list]
print(vswr_list)

# Load the VSWR data into a DataFrame indexed by the frequdency
df = pd.DataFrame(vswr_list, index=frequency_list)
print(df)
# Re-sample using the start/end/step provided by the user.  Linear
# interpolation is automatically used
df1 = df.reindex(frequency_space).interpolate()
print(df1)
v = [column[0] for column in df1.values.tolist()]
print(v)
i = df1.index.tolist()
print(i)


