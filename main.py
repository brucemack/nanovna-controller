from jinja2 import Template
import numpy as np
import pandas as pd
import serial
import nanovna as nv
from flask import Flask, request, make_response, send_from_directory, send_file, jsonify
import json
import logging

ser = None

config = {
    "listen_host": "localhost",
    "listen_port": 8080
}

user_config = {
    "port": "/dev/cu.usbmodem4001",
}




logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
app = Flask(__name__)
nanovna = nv.Nanovna()

@app.route("/static/<filename>")
def root2(filename):
    return send_file("static/" + filename)


@app.route("/")
def root():
    return send_file("static/index.html")

@app.route("/api/sweep", methods=["GET", "POST"])
def sweep():
    try:
        # Get connected to the NanoVNA
        nanovna.connect_if_necessary(user_config["port"])

        # Process request parameters
        if request.args.get("cal_preset").strip() == "":
            raise Exception("Calibration preset is missing")
        cal_preset = int(request.args.get("cal_preset"))
        if request.args.get("start_frequency_mhz").strip() == "":
            raise Exception("Start frequency is missing")
        try:
            start_frequency = int(float(request.args.get("start_frequency_mhz")) * 1000000)
        except Exception as ex:
            raise Exception("Invalid start frequency: " + str(ex))
        if request.args.get("end_frequency_mhz").strip() == "":
            raise Exception("End frequency is missing")
        try:
            end_frequency = int(float(request.args.get("end_frequency_mhz")) * 1000000)
        except Exception as ex:
            raise Exception("Invalid end frequency: " + str(ex))
        if start_frequency >= end_frequency:
            raise Exception("Frequency range was not valid")
        if request.args.get("step_frequency_mhz").strip() == "":
            step_count = 10
            step_frequency = (end_frequency - start_frequency) / step_count
        else:
            try:
                step_frequency = int(float(request.args.get("step_frequency_mhz")) * 1000000)
                if step_frequency < 0:
                    raise Exception("Step must be positive")
            except Exception as ex:
                raise Exception("Invalid step: " + str(ex))
            step_count = int((end_frequency - start_frequency) / step_frequency)
        if step_count > 50:
            raise Exception("There are too many steps")
        if step_count == 0:
            raise Exception("There are not enough steps")

        nanovna.run_command("info")
        nanovna.run_command("recall " + str(cal_preset))
        # Set the sweep range
        nanovna.run_command("sweep " + str(start_frequency) + " " + str(end_frequency))
        # Get the battery voltage in volts
        #vbat_lines = nv.run_command(ser, "vbat")
        #vbat = float(vbat_lines[0][:-2]) / 1000
        # Collect the frequencies of the sweep
        lines = nanovna.run_command("frequencies")
        frequency_list = [float(line) for line in lines]
        # Make the VSWR data
        rc_list = nanovna.get_complex_data()
        # Convert to VSWR
        vswr_list = [nanovna.reflection_coefficient_to_vswr(rc) for rc in rc_list]
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

        # Format the result
        result = {
            "error": False,
            "headers": ["{:.03f}".format(f / 1000000.0) for f in result_frequencies],
            "rows": [
                {
                    "header": "VSWR",
                    "cells": ["{:.02f}".format(v) for v in result_vswrs]
                }
            ]
        }
        # Tweak the minimum VSWR with the best match annotation
        result.get("headers")[min_index] = result.get("headers")[min_index] + " best match"
        result.get("rows")[0].get("cells")[min_index] = result.get("rows")[0].get("cells")[min_index] + " best match"

        return jsonify(result)

    except Exception as ex:
        logging.error("Error in sweep", exc_info=True)
        result = {
            "error": True,
            "message": ex.args[0]
        }
        return jsonify(result)


if __name__ == "__main__":
    app.run(host=config["listen_host"], port=config["listen_port"])

