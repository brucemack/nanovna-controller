from jinja2 import Template
import numpy as np
import pandas as pd
import serial
import nanovna as nv
from flask import Flask, request, make_response
import json

# This is the template that renders the main sweep screen
template_sweep_text = """
<html>
    <head>
        <title>NanoVNA Control Panel</title>
        <style>
        table {
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid black;
        }
        </style>
    </head>
    <body>
        <h1>NanoVNA Control Panel</h1>
        <p>The NanoVNA is connected</p>
        <form method="post" action="/">
            <label for="s1">Start Frequency in Megahertz</label>
            <input type="text" id="s1" name="start_frequency_mhz" value="{{ start_frequency_mhz }}"/>
            <label for="s2">End Frequency in Megahertz</label>
            <input type="text" id="s2" name="end_frequency_mhz" value="{{ end_frequency_mhz}}"/>
            <label for="s3">Step in Megahertz</label>
            <input type="text" id="s3" name="step_frequency_mhz" value="{{ step_frequency_mhz}}"/>
            <button>Sweep</button>
        </form>
        <table>
            <caption>VSWR Sweep Results</caption>
            <thead>
                <tr>
                    {% for freq in freqs %}
                    <th>{{ freq }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                <tr>
                    {% for vswr in vswrs %}
                    <td> {{ vswr }}</td>
                    {% endfor %}
                </tr>
            </tbody>
        </table>
        <p>NanoVNA voltage is {{ voltage }} volts</p>
    </body>
</html>
"""

template_sweep = Template(template_sweep_text)
ser = None


def connect_if_necessary():
    global ser
    if ser is None:
        print("Connection is not open")
        # Open the serial port to the NanoVNA
        ser = serial.Serial('/dev/cu.usbmodem4001')
    else:
        print("Connection is good")


state = {
    "start_frequency_mhz": 28,
    "end_frequency_mhz": 30,
    "step_frequency_mhz": 0.25
}

listen_host = "localhost"
listen_port = 8080

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def sweep():

    global state

    try:
        # Look for post variables
        if request.method == "POST":
            state["start_frequency_mhz"] = request.form["start_frequency_mhz"]
            state["end_frequency_mhz"] = request.form["end_frequency_mhz"]
            state["step_frequency_mhz"] = request.form["step_frequency_mhz"]
        elif request.method == "GET":
            if "sweep_state" in request.cookies:
                print("Cookie received")
                state = json.loads(request.cookies.get("sweep_state"))

        print(state)
        connect_if_necessary()

        # Test
        start_frequency = int(float(state["start_frequency_mhz"]) * 1000000)
        end_frequency = int(float(state["end_frequency_mhz"]) * 1000000)
        step_frequency = int(float(state["step_frequency_mhz"]) * 1000000)
        step_count = int((end_frequency - start_frequency) / step_frequency)

        if start_frequency >= end_frequency or step_count > 50:
            print("Range error")
            raise Exception("Frequency range error")

        nv.run_command(ser, "info")
        # Set the sweep range
        nv.run_command(ser, "sweep " + str(start_frequency) + " " + str(end_frequency))
        # Get the battery voltage in volts
        vbat_lines = nv.run_command(ser, "vbat")
        vbat = float(vbat_lines[0][:-2]) / 1000
        # Collect the frequencies of the sweep
        lines = nv.run_command(ser, "frequencies")
        frequency_list = [float(line) for line in lines]
        # Make the VSWR data
        rc_list = nv.get_complex_data(ser)
        # Convert to VSWR
        vswr_list = [nv.reflection_coefficient_to_vswr(rc) for rc in rc_list]
        # Load the VSWR data into a DataFrame indexed by the frequency
        df = pd.DataFrame(vswr_list, index=frequency_list)
        # Re-sample using the start/end/step provided by the user.  Linear
        # interpolation is automatically used
        frequency_space = np.linspace(start_frequency, end_frequency - step_frequency, step_count)
        df1 = df.reindex(frequency_space).interpolate()
        # Pull out index values
        result_frequencies = df1.index.tolist()
        # Pull out VSWR values
        result_vswrs = [column[0] for column in df1.values.tolist()]
        # Find the lowest value
        min_vswr = min(result_vswrs)
        # Determine which index the minimum belongs to
        min_index = result_vswrs.index(min_vswr)
        # Format
        formatted_frequencies = ["{:.03f}".format(f / 1000000.0) for f in result_frequencies]
        formatted_vswrs = ["{:.02f}".format(v) for v in result_vswrs]
        # Tweak the minimum VSWR with the best match annotation
        formatted_frequencies[min_index] = formatted_frequencies[min_index] + " best match"
        formatted_vswrs[min_index] = formatted_vswrs[min_index] + " best match"
        formatted_voltage = "{:.01f}".format(vbat)

        a = {
            'freqs': formatted_frequencies,
            'vswrs': formatted_vswrs,
            'start_frequency_mhz': state["start_frequency_mhz"],
            'end_frequency_mhz': state["end_frequency_mhz"],
            'step_frequency_mhz': state["step_frequency_mhz"],
            'voltage': formatted_voltage
        }

        response = make_response(template_sweep.render(a))
        # Store the state for future usage
        response.set_cookie("sweep_state", json.dumps(state))

        return response

    except Exception as ex:
        print("Error", ex)
        return "Error"


if __name__ == "__main__":
    app.run(host=listen_host, port=listen_port)

