from jinja2 import Template
import numpy as np
import pandas as pd
import serial
import nanovna as nv
from flask import Flask, request, make_response, send_from_directory, send_file, jsonify
import json
import logging
import configparser
import sys

# Configure logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# Get static location
if len(sys.argv) < 2:
    logging.error("Argument error")
    sys.exit(-1)

base_dir = sys.argv[1]
logging.info("NanoVNA Controller")
logging.info("Base Directory is " + base_dir)

# Load .ini file
config = configparser.ConfigParser()
config.read(base_dir + "/config.ini")
static_config = config["DEFAULT"]

logging.info("Working directory is " + static_config["workdir"])

user_config = { }

def load_user_config():
    global user_config
    try:
        with open(static_config["workdir"] + "/userconfig.json") as f:
            user_config = json.load(f)
            logging.info("Loaded user configuration")
            logging.info(user_config)
    except Exception as ex:
        logging.warning("Unable to read user configuration")
        user_config = {}

    # Program some defaults
    if not ("port" in user_config):
        user_config["port"] = "COM3"


def save_user_config():
    with open(static_config["workdir"] + "/userconfig.json", "w") as f:
        json.dump(user_config, f)
        logging.info("Saved user configuration")
        logging.info(user_config)


# Initial load of configuration properties
load_user_config()

nanovna = nv.Nanovna()

# Flask routes
app = Flask(__name__)


@app.route("/static/<filename>")
def root2(filename):
    return send_file(base_dir + "/static/" + filename)


@app.route("/")
def root():
    """ Sends static home page. """
    return send_file(base_dir + "/static/index.html")


@app.route("/api/config", methods=["GET", "POST"])
def config():
    """ Allows the client to read and write the user configuration parameters. """
    if request.method == "POST":
        for item in request.form.items():
            user_config[item[0]] = item[1]
            logging.info("Changed config value " + item[0] + "=" + item[1])
        save_user_config()
    return jsonify(user_config)


@app.route("/api/calibrate", methods=["GET"])
def calibrate():

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

        # On step 0 we set the range and reset
        if request.args["step"] == "0":
            logging.info("Calibration step 0")
            # Set the sweep range
            nanovna.run_command("sweep " + str(start_frequency) + " " + str(end_frequency))
            # Reset
            nanovna.run_command("cal reset")
            # Cal short
            nanovna.run_command("cal short")
        elif request.args["step"] == "1":
            logging.info("Calibration step 1")
            # Cal open
            nanovna.run_command("cal open")
        elif request.args["step"] == "2":
            logging.info("Calibration step 2")
            # Cal load
            nanovna.run_command("cal load")
            # Cal done
            nanovna.run_command("cal done")
            # Save
            nanovna.run_command("save " + request.args["cal_preset"])

        return "OK"

    except Exception as ex:
        logging.error("Error in calibration", exc_info=True)
        result = {
            "error": True,
            "message": ex.args[0]
        }
        return jsonify(result)


@app.route("/api/status", methods=["GET"])
def status():

    try:
        # Get connected to the NanoVNA
        nanovna.connect_if_necessary(user_config["port"])
        # Execute various status commands
        vbat_lines = nanovna.run_command("vbat")
        vbat = float(vbat_lines[0][:-2]) / 1000
        version_lines = nanovna.run_command("version")

        result = {
            "version": version_lines[0],
            "voltage": vbat
        }
        return result

    except Exception as ex:
        logging.error("Error in status", exc_info=True)
        result = {
            "error": True,
            "message": ex.args[0]
        }
        return jsonify(result)


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
    app.run(host=static_config["listenhost"], port=static_config["listenport"])
